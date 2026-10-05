"""Gaia2 (ARE 1.2.0) harness for the BIT pipeline (docs/design/GAIA2_ADAPTER_PLAN.md, U4): the AppWorld H1.1 harness
(bos_appworld_v3.py) on a deterministic, synchronously ticked ARE environment. One python cell per step calling App__tool(...)
functions; AgentUserInterface__send_message_to_user ends a turn. Every step (live, no_exec or replayed) advances the virtual clock by
G2_GEN_SECONDS before executing; free re-asks cost neither a step nor clock time, so the clock is a function of the code sequence.
Hook order (= boost/bit_rubric._simulate). Live step k: state _step/_tid/_replay_len -> pre_call -> LLM (<= 3 free re-asks per step,
12 per episode) -> no valid code: no_exec step (advance, tick, pull; no post_parse / post_exec) | post_parse -> pre_complete (only if
the cell calls send_message_to_user) -> advance, exec, tick, [idle_until_message if a turn ended and turns remain], pull -> out =
exec output + notification block -> post_exec. Replayed step (BOS_REPLAY items: code str | {"exec", "shown"} | "" = no exec): no
pre_call / post_parse; same advance/exec/tick/idle/pull; post_exec for every item.
usage: python bos_gaia2.py eval --patch P|none --seed S --tag T --workers W [--n-games N] [--replay-only]   (tasks: BOS_TASKS)
       python bos_gaia2.py selftest --result R.json [--n 10] [--twice]
Test seams (local tests only): G2_ENV_FACTORY="module:fn" fn(tid, seed, gen_seconds) -> G2Env-like object; G2_CLIENT_FACTORY=
"module:fn" fn() -> OpenAI-like client."""
import argparse, importlib, json, os, re, subprocess, sys, time
from datetime import datetime, timezone
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import g2_hooks as Hk

FREE_RETRIES_STEP, FREE_RETRIES_EP = 3, 12
END_REASONS = ("turns_done", "env_stopped", "time_up", "budget", "crashed", "replay_end")
NO_EXEC_OUT = "Nothing was executed this step."


def _cfg(over=None):
    c = {"max_steps": int(os.environ.get("G2_STEPS", "40")), "gen_seconds": float(os.environ.get("G2_GEN_SECONDS", "1.0")),
         "hist": int(os.environ.get("G2_HIST", "20")), "ep_timeout": float(os.environ.get("G2_EP_TIMEOUT", "3600")),
         "cell_timeout": float(os.environ.get("G2_CELL_TIMEOUT", "30")), "max_tokens": int(os.environ.get("BOS_MAX_TOKENS", "8192")),
         "think": os.environ.get("BOS_THINK_OFF", "0") != "1", "model": os.environ.get("BOS_MODEL", "qwen/qwen3-30b-a3b-instruct-2507"),
         "temperature": float(os.environ.get("BOS_TEMPERATURE", "0.4")), "out": os.environ.get("G2_OUT", HERE),
         "prompt_chars": int(os.environ.get("G2_PROMPT_CHARS", "60000"))}
    c.update(over or {}); return c


def _load_attr(spec):
    mod, _, attr = spec.partition(":"); return getattr(importlib.import_module(mod), attr)


# ---------------------------------------------------------------- environment + LLM
def _make_env(tid, seed, cfg):
    """-> (env, judge). Imports first, then install_determinism (patches the loaded are.simulation modules), then ARE objects."""
    fac = os.environ.get("G2_ENV_FACTORY")
    if fac: return _load_attr(fac)(tid, seed, cfg["gen_seconds"]), None
    import g2_env as E, g2_judge as J
    E.install_determinism(); E.begin_episode(tid, seed)
    judge = J.judge_engine_from_env(); config, sj = E.load_scenario_json(tid)
    try: env = E.G2Env(sj, judge, gen_seconds=cfg["gen_seconds"], tid=tid, seed=seed, config=config)
    except TypeError as e:   # a G2Env without the optional config keyword (plan signature)
        if "config" not in str(e): raise
        env = E.G2Env(sj, judge, gen_seconds=cfg["gen_seconds"], tid=tid, seed=seed)
    if getattr(env, "config", None) is None:
        try: env.config = config
        except Exception: pass
    return env, judge


def _api_key():
    k = os.environ.get("BOS_API_KEY")
    if not k and os.path.exists("/root/autodl-tmp/vllm_api_key"): k = open("/root/autodl-tmp/vllm_api_key").read().strip()
    return k or os.environ.get("OPENROUTER_API_KEY") or "EMPTY"


def _make_client():
    fac = os.environ.get("G2_CLIENT_FACTORY")
    if fac: return _load_attr(fac)()
    from openai import OpenAI
    return OpenAI(api_key=_api_key(), base_url=os.environ.get("BOS_BASE_URL", "https://openrouter.ai/api/v1"), timeout=float(os.environ.get("BOS_TIMEOUT", "60")), max_retries=0)


def backbone_extra():
    extra = {}
    if os.environ.get("BOS_TOP_K"): extra["top_k"] = int(os.environ["BOS_TOP_K"])
    if os.environ.get("BOS_THINK_OFF") == "1": extra["chat_template_kwargs"] = {"enable_thinking": False}
    return extra or None


CTX_ERR = re.compile(r"maximum context length|context length exceeded|too many tokens|is longer than the model", re.I)


def shrink_msgs(msgs):
    """drop the oldest history pair: msgs = [system, task turn, (assistant, user)*, ...] -> without msgs[2:4]."""
    return msgs[:2] + msgs[4:]


def fit_msgs(msgs, max_chars):
    """drop the oldest history pairs until the prompt is at most max_chars characters (the last user turn is always kept)."""
    n = sum(len(m["content"]) for m in msgs)
    while n > max_chars and len(msgs) >= 5:
        n -= len(msgs[2]["content"]) + len(msgs[3]["content"]); msgs = shrink_msgs(msgs)
    return msgs


class LLM:
    def __init__(self, cfg, temperature):
        from g2_exec import strip_think
        self.cfg, self.T, self.strip_think = cfg, temperature, strip_think; self.client = _make_client(); self.extra = backbone_extra()
        self.sampling = {"top_p": float(os.environ["BOS_TOP_P"])} if os.environ.get("BOS_TOP_P") else {}
        self.tok = [0, 0]; self.calls = 0; self.errors = 0

    def chat(self, msgs, si):
        """-> (answer after </think>, thinking) or None if all 6 attempts failed (bos_appworld_v3 retry / backoff / reconnect).
        A context-length rejection (HTTP 400) is not retried as is: the oldest history pair is dropped (shrink_msgs), or, with no history
        left, max_tokens is halved (>= 1024); immediately, without backoff, and not counted as an API retry (si["ctx_trim"])."""
        r = None; last = None; att = 0; max_tokens = self.cfg["max_tokens"]; n_trim = 0
        while att < 6:
            try:
                r = self.client.chat.completions.create(model=self.cfg["model"], messages=msgs, temperature=self.T, max_tokens=max_tokens, n=1, extra_body=self.extra, **self.sampling); break
            except Exception as e:
                if CTX_ERR.search(str(e)) and n_trim < 40:
                    n_trim += 1; si["ctx_trim"] = si.get("ctx_trim", 0) + 1
                    if len(msgs) >= 5: msgs = shrink_msgs(msgs); continue
                    if max_tokens > 1024: max_tokens = max(1024, max_tokens // 2); si["max_tokens_cut"] = max_tokens; continue   # vLLM reports only a lower bound of the input tokens
                last = e; si["api_retries"] = si.get("api_retries", 0) + 1; att += 1
                if "402" in str(e): raise
                try: self.client = _make_client()
                except Exception: pass
                time.sleep(min(30, 2 * (2 ** (att - 1))))
        if r is None:
            self.errors += 1; si["api_error"] = str(last)[:80]; return None
        m = r.choices[0].message; u = getattr(r, "usage", None); self.calls += 1
        if u is not None: self.tok[0] += getattr(u, "prompt_tokens", 0) or 0; self.tok[1] += getattr(u, "completion_tokens", 0) or 0
        answer, think = self.strip_think(m.content or "")
        rc = getattr(m, "reasoning_content", None) or ""
        return answer, (rc + ("\n" + think if think else "")) if rc else think


# ---------------------------------------------------------------- prompt
SYSTEM = """You are an assistant that operates a user's phone through its apps. You act by writing Python code.
Rules:
- Reply with exactly ONE ```python code block per message (keep any reasoning before it short). The block is executed and its output is shown to you in the next message.
- Every app tool is a Python function named App__tool; call it with keyword arguments, e.g. result = App__tool(arg=value). Tools return values: print what you need to see.
- Variables persist between cells. help("App__tool") prints the full documentation of a tool.
- AgentUserInterface__send_message_to_user(content=...) is the ONLY way to reply to the user, and it ENDS your turn. Send exactly one message per user request, after you have done everything the request asks (or one clarifying question if the request is ambiguous). Never send progress updates.
- Use SystemApp__wait_for_notification(timeout=...) to wait for time-based events or for replies from other people.
- Do only what the user asked; every write action you take is checked.
- Budget: {max_steps} steps (code cells) in total, across all turns of the conversation. Each output ends with the number of steps used.

Available tools (* = required argument):
{index}"""


def _notif_prompt(env):
    f = getattr(env, "notification_prompt", None)
    if callable(f):
        try: return f() or ""
        except Exception: return ""
    try:
        from are.simulation.agents.default_agent.prompts.notification_system import get_notification_system_prompt
        are_env = getattr(env, "env", None); ns = getattr(env, "notification_system", None) or getattr(are_env, "notification_system", None)
        apps = getattr(getattr(env, "scenario", None), "apps", None) or (list(are_env.apps.values()) if are_env is not None and isinstance(getattr(are_env, "apps", None), dict) else None)
        return get_notification_system_prompt(ns, apps) if ns is not None else ""
    except Exception: return ""


def system_prompt(env, tools, max_steps, format_tool_index):
    parts = [SYSTEM.format(max_steps=max_steps, index=format_tool_index(tools)), _notif_prompt(env), getattr(env, "additional_system_prompt", None) or ""]
    return "\n\n".join(p.strip() for p in parts if p and p.strip())


def out_cap(code): return 8000 if "help(" in code else 3000


def out_view(code, out):
    """the output text the model sees (H1.1): never cut silently -- say how much is missing and which tools a listing lost."""
    cap = out_cap(code); shown = out[:cap]
    if len(out) > cap:
        rest = out[cap:] if out[cap - 1] == "\n" else out[cap:].partition("\n")[2]   # skip a line cut in the middle (no name fragments)
        cut = re.findall(r"^\s*([A-Za-z0-9]+__[A-Za-z0-9_]+)\(", rest, re.M)
        shown += f"\n[harness] output truncated: {len(out) - cap} more characters not shown"
        if cut: shown += f"; tools not shown: {', '.join(cut[:60])}" + (" ..." if len(cut) > 60 else "") + " (use help(\"App__tool\") or print a smaller part)"
    return shown


def fmt_time(t): return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def render_messages(m, skip_user=None):
    """pull_messages() dict -> notification block: user messages first ("[user message] ..."), then "[time] msg" notifications."""
    users = []
    for u in (m or {}).get("user") or []:
        txt = u if isinstance(u, str) else str((u or {}).get("content") or (u or {}).get("message") or u)
        if skip_user is not None and txt.strip() == skip_user.strip(): skip_user = None; continue
        users.append("[user message] " + txt)
    return "\n".join(users + [str(x) for x in (m or {}).get("notifications") or []])


def join_out(exec_out, block):
    """block appended AFTER the output, so an 'Execution failed' prefix is preserved."""
    if not block: return exec_out
    return exec_out + ("\n" if exec_out and not exec_out.endswith("\n") else "") + block


# ---------------------------------------------------------------- one episode
def play(job):
    cfg = job["cfg"]; tid, seed = job["tid"], job["seed"]; pre = job.get("replay") or []; t0 = time.time(); MAX = cfg["max_steps"]
    env, judge = _make_env(tid, seed, cfg)
    from g2_exec import CodeExecutor, extract_code, validate_code, format_tool_index
    funcs, consts = Hk.load_patch(job.get("patch"), quiet=True)
    H = int(consts.get("HISTORY_LENGTH", cfg["hist"])); T = float(consts.get("TEMPERATURE", cfg["temperature"]))
    llm = None if job.get("replay_only") else LLM(cfg, T)
    tools = env.tools(); ex = CodeExecutor(tools, cell_timeout_s=cfg["cell_timeout"], clock=env.now)   # time / datetime in cells read the virtual clock
    sysmsg = system_prompt(env, tools, MAX, format_tool_index)
    state = {}; traj = []; hist = []; free_used = 0; steps = 0; end = None; crashed = None; instr = ""
    if job.get("hint"): state["_hint"] = job["hint"]

    def stamp(k): return f"\n[{k + 1} of {MAX} steps used]"

    def run_cell(code):
        """advance -> exec (code None: nothing) -> tick -> idle if a turn ended and turns remain -> pull."""
        n0 = env.turns_done(); env.advance(cfg["gen_seconds"]); info = {"calls": [], "writes": 0, "exc": None}; exec_out = None
        if code is not None:
            try: exec_out, info = ex.run(code)
            except Exception as e: exec_out = f"Execution failed. {type(e).__name__}: {str(e)[:300]}"; info = {"calls": [], "writes": 0, "exc": "env_exc"}
        env.tick(); n1 = env.turns_done()
        if n1 > n0 and n1 < env.nb_turns: env.idle_until_message(max(0.0, env.start_time + env.duration - env.now()))
        if exec_out and hasattr(env, "scrub"): exec_out = env.scrub(exec_out)   # no per-process sandbox paths in what the model sees
        return exec_out or "", info or {}, env.pull_messages()

    def ended(m):
        if env.turns_done() >= env.nb_turns: return "turns_done"
        if (m or {}).get("stop") or env.stopped(): return "env_stopped"
        if env.time_up(): return "time_up"
        return None

    def rec(step, code, out, block, info, **kw):
        return {"step": step, "code": code, "out": out[:200], "exec_error": int(out.startswith("Execution failed")), "t_sim": round(env.now() - env.start_time, 3),
                "notif": block[:300], "calls": list(info.get("calls") or [])[:20], "writes": int(info.get("writes") or 0), "gp": None, "gf": None, **kw}

    try:
        setup_codes = ([str(consts["SETUP_CODE"])] if consts.get("SETUP_CODE") else []) + Hk.run_setup(funcs, state)
        for sc in setup_codes:
            try: state["_setup_out"] = str(ex.run(sc)[0])[:300]
            except Exception as e: state["_setup_out"] = f"setup error {e}"[:300]
        init = env.pull_messages(); instr = env.first_task(); state["_instr"] = instr
        extra = render_messages(init, skip_user=instr)   # the task message itself arrives via pull_messages; shown once, in the task turn
        task_msg = f"Current time: {fmt_time(env.now())}\nTask: {instr}" + ("\n" + extra if extra else "")
        end = ended(init); step = 0
        while end is None and step < MAX:
            if time.time() - t0 > cfg["ep_timeout"]: crashed = f"EpisodeTimeout: wall clock over {cfg['ep_timeout']:.0f}s"; end = "crashed"; break
            if step < len(pre):   # exact replay of a logged prefix: no LLM call, no pre_call / post_parse
                it = pre[step]; code, shown = (it.get("exec") or "", it.get("shown")) if isinstance(it, dict) else (it or "", None)
                noex = not code.strip()
                exec_out, info, m = run_cell(None if noex else code); block = render_messages(m)
                out = join_out(NO_EXEC_OUT if noex else exec_out, block)
                Hk.run_post_exec(funcs, code, out, state)
                traj.append(rec(step, code, out, block, info, resp="", replayed=1, no_exec=int(noex), code_final=code[:300], free_retries=0, pc=0,
                                **({"shown": str(shown)[:300]} if shown is not None else {})))
                a_txt = "(empty reply)" if noex and shown is None else "```python\n" + (code if shown is None else str(shown)) + "\n```"
                hist.append((a_txt, "Output:\n```\n" + out_view(code, out) + "\n```" + stamp(step)))
            elif job.get("replay_only"): end = "replay_end"; break
            else:
                msgs = [{"role": "system", "content": sysmsg}, {"role": "user", "content": task_msg}]
                for a_txt, u_out in (hist[-H:] if H > 0 else []): msgs += [{"role": "assistant", "content": a_txt}, {"role": "user", "content": u_out}]
                msgs = fit_msgs(msgs, cfg["prompt_chars"])   # 32k-token context: max_tokens (8192) + system (~19k chars) + history must fit
                si = {}; state["_step"], state["_tid"], state["_replay_len"] = step, tid, len(pre)
                prompt0 = msgs[-1]["content"]; prompt = Hk.run_text(funcs, "pre_call", prompt0, state, si)
                si["pc"] = int(prompt != prompt0); msgs[-1] = {"role": "user", "content": prompt}
                got = llm.chat(msgs, si); answer = got[0] if got else ""
                code = extract_code(answer); why = validate_code(code); n_free = 0
                while why and n_free < FREE_RETRIES_STEP and free_used < FREE_RETRIES_EP:   # never execute missing / truncated / placeholder code
                    n_free += 1; free_used += 1
                    fb = (f"Nothing was executed: {why}. Your variables and all app state are unchanged and this did not use up a step. "
                          f"Reply with ONE complete ```python code block now (keep any reasoning short).")
                    got = llm.chat(msgs + [{"role": "assistant", "content": answer[-4000:] or "(empty reply)"}, {"role": "user", "content": fb}], si)
                    if got is None: break
                    answer = got[0]; code = extract_code(answer); why = validate_code(code)
                si["free_retries"] = n_free
                if why:   # free re-asks exhausted: spend the step (clock moves), execute nothing, and say so
                    si["invalid_code"] = why[:80]
                    exec_out, info, m = run_cell(None); block = render_messages(m)
                    out = join_out(f"{NO_EXEC_OUT[:-1]}: {why}. Variables and app state are unchanged.", block)
                    traj.append(rec(step, "", out, block, info, resp=answer[-600:], replayed=0, no_exec=1, code_final="", **si))
                    hist.append((answer[-4000:] or "(empty reply)", "Output:\n```\n" + out + "\n```" + stamp(step)))
                else:
                    code = Hk.run_text(funcs, "post_parse", code, state, si)
                    if Hk.PRE_COMPLETE_MARKER in code: code = Hk.run_text(funcs, "pre_complete", code, state, si)
                    exec_out, info, m = run_cell(code); block = render_messages(m); out = join_out(exec_out, block)
                    Hk.run_post_exec(funcs, code, out, state, si)
                    traj.append(rec(step, code, out, block, info, resp=answer[-600:], replayed=0, no_exec=0, code_final=code[:300], **si))
                    hist.append((answer or "```python\n" + code + "\n```", "Output:\n```\n" + out_view(code, out) + "\n```" + stamp(step)))
            step += 1; steps += 1; end = ended(m)
        if end is None: end = "budget"
    except Exception as e:
        import traceback
        crashed = f"{type(e).__name__}: {str(e)[:200]}"; end = "crashed"; state["_tb"] = traceback.format_exc()[-1500:]
    try: sh = env.state_hash()
    except Exception as e: sh = f"error {type(e).__name__}"
    try: v = env.validate() or {}
    except Exception as e: v = {"success": False, "rationale": f"validate exception {type(e).__name__}: {str(e)[:200]}", "exception": f"{type(e).__name__}: {str(e)[:200]}"}
    try: nb, td = env.nb_turns, env.turns_done()
    except Exception: nb, td = None, None
    return {"task": tid, "won": bool(v.get("success")), "G": v.get("G"), "harm_fail": None, "steps": steps, "traj": traj, "crashed": crashed,
            "config": getattr(env, "config", None), "instr": instr, "rationale": v.get("rationale"), "rationale_diag": v.get("rationale_diag"),
            "end_reason": end, "nb_turns": nb, "turns_done": td, "state_hash": sh, "agent_counts": v.get("agent_counts"), "oracle_counts": v.get("oracle_counts"),
            "n_oracle_writes": v.get("n_oracle_writes"), "validate_exception": v.get("exception"), "fired": state.get("_cc_fired", []),
            "setup_err": state.get("_edit_err"), "traceback": state.get("_tb"), "free_used": free_used,
            "bb": [llm.calls, llm.errors, llm.tok[0], llm.tok[1]] if llm else [0, 0, 0, 0],
            "judge": [int(getattr(judge, "hits", 0) or 0), int(getattr(judge, "misses", 0) or 0)], "wall_s": round(time.time() - t0, 1)}


def _crashed_ep(tid, e):
    return {"task": tid, "won": False, "G": None, "harm_fail": None, "steps": 0, "traj": [], "crashed": f"{type(e).__name__}: {str(e)[:200]}",
            "config": None, "instr": "", "rationale": None, "rationale_diag": None, "end_reason": "crashed", "nb_turns": None, "turns_done": None,
            "state_hash": None, "agent_counts": None, "oracle_counts": None, "n_oracle_writes": None, "validate_exception": None, "fired": [],
            "setup_err": None, "traceback": None, "free_used": 0, "bb": [0, 0, 0, 0], "judge": [0, 0], "wall_s": 0.0}


def _worker(job):
    """process-pool entry (one episode per process): an exception marks the episode crashed instead of aborting the pass."""
    try: return job["i"], play(job)
    except Exception as e:
        import traceback
        r = _crashed_ep(job["tid"], e); r["traceback"] = traceback.format_exc()[-1500:]; return job["i"], r


# ---------------------------------------------------------------- run
def run_eval(patch_path, seed, tag, n_games=None, workers=4, replay_only=False, tasks=None, replay=None, hints=None, cfg_over=None, write=True):
    cfg = _cfg(cfg_over)
    if tasks is None: tasks = json.load(open(os.environ["BOS_TASKS"], encoding="utf-8"))
    tasks = list(tasks)[: (n_games or 10 ** 9)]
    if replay is None: replay = json.load(open(os.environ["BOS_REPLAY"], encoding="utf-8")) if os.environ.get("BOS_REPLAY") else {}
    if hints is None: hints = json.load(open(os.environ["BOS_HINTS"], encoding="utf-8")) if os.environ.get("BOS_HINTS") else {}
    _, consts = Hk.load_patch(patch_path)   # validate (and announce) once in the parent
    os.environ["PYTHONHASHSEED"] = "0"   # spawned workers inherit it (App.set_seed uses hash())
    jobs = [{"i": i, "tid": t, "seed": seed, "patch": patch_path, "replay": replay.get(t) or [], "hint": hints.get(t), "replay_only": replay_only, "cfg": cfg}
            for i, t in enumerate(tasks)]
    results = [None] * len(tasks); t0 = time.time()

    def done(i, r):
        results[i] = r
        print(f"  [{sum(x is not None for x in results)}/{len(tasks)}] {r['task']} won={int(r['won'])} G={r['G']} steps={r['steps']} end={r['end_reason']}"
              + (f" crashed={r['crashed']}" if r["crashed"] else "") + f" t={time.time() - t0:.0f}s", flush=True)
    if workers <= 0:   # in-process, serial (debugging only: no per-episode process isolation)
        for j in jobs: done(*_worker(j))
    else:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
            for fut in as_completed([ex.submit(_worker, j) for j in jobs]): done(*fut.result())
    n = len(results); G = [r["G"] for r in results if r["G"] is not None]
    H = int(consts.get("HISTORY_LENGTH", cfg["hist"])); T = float(consts.get("TEMPERATURE", cfg["temperature"]))
    res = {"tag": tag, "patch": patch_path, "seed": seed, "bench": "gaia2", "model": cfg["model"], "history_length": H, "temperature": T, "parse_unclosed": False,
           "harness_v2": True, "harness_h1": True, "harness_h11": True, "no_eval": True, "max_steps": cfg["max_steps"], "gen_seconds": cfg["gen_seconds"],
           "think": cfg["think"], "instructions": "bos_gaia2.SYSTEM", "max_tokens": cfg["max_tokens"], "backbone_extra": backbone_extra(), "replay_only": bool(replay_only),
           "judge_model": os.environ.get("G2_JUDGE_MODEL", os.environ.get("BOS_MODEL")), "judge_hits": sum(r["judge"][0] for r in results), "judge_misses": sum(r["judge"][1] for r in results),
           "n_games": n, "success_rate": sum(r["won"] for r in results) / max(n, 1), "mean_G": sum(G) / max(len(G), 1),
           "won": [r["won"] for r in results], "G": [r["G"] for r in results], "harm_fail": [None] * n, "games": [r["task"] for r in results], "steps": [r["steps"] for r in results],
           "crashed": [r["crashed"] for r in results], "traj": [r["traj"] for r in results],
           **{k: [r[k] for r in results] for k in ("instr", "rationale", "rationale_diag", "end_reason", "nb_turns", "turns_done", "state_hash", "agent_counts",
                                                  "oracle_counts", "n_oracle_writes", "validate_exception", "fired", "setup_err", "traceback", "free_used", "wall_s")},
           "configs": [r["config"] for r in results],
           "calls": sum(r["bb"][0] for r in results), "api_errors": sum(r["bb"][1] for r in results), "tokens_in": sum(r["bb"][2] for r in results),
           "tokens_out": sum(r["bb"][3] for r in results), "finished": time.strftime("%Y-%m-%d %H:%M")}
    if write:
        os.makedirs(os.path.join(cfg["out"], "results"), exist_ok=True); path = os.path.join(cfg["out"], "results", f"{tag}_seed{seed}.json")
        with open(path, "w", encoding="utf-8") as f: json.dump(res, f, default=str)
        res["_path"] = path
    print(f"{tag} seed{seed}: success {res['success_rate']:.3f} mean_G {res['mean_G']:.2f} calls {res['calls']} api_errors {res['api_errors']} "
          f"judge hits/misses {res['judge_hits']}/{res['judge_misses']}", flush=True)
    return res


# ---------------------------------------------------------------- selftest
def replay_items(traj):
    """logged steps -> BOS_REPLAY items: executed code; "" for no_exec steps; {"exec", "shown"} for replayed blocked cells."""
    items = []
    for s in traj:
        code = s.get("code") or ""
        if s.get("no_exec") or not code: items.append("")
        elif s.get("replayed") and "shown" in s: items.append({"exec": code, "shown": s["shown"]})
        else: items.append(code)
    return items


def compare_eps(a, b, ta, tb):
    """a = reference episode (fields as in the result JSON), b = replay. -> list of mismatch strings."""
    mm = []
    if len(ta) != len(tb): mm.append(f"n_steps {len(ta)} vs {len(tb)}")
    for s, t in zip(ta, tb):
        k = s.get("step")
        if s.get("t_sim") != t.get("t_sim"): mm.append(f"step {k} t_sim {s.get('t_sim')} vs {t.get('t_sim')}")
        if s.get("no_exec") and not s.get("replayed"):   # live no_exec text names the reason; its replay ("" item) does not
            if (s.get("notif") or "") != (t.get("notif") or ""): mm.append(f"step {k} notif {s.get('notif')!r} vs {t.get('notif')!r}")
        elif (s.get("out") or "")[:200] != (t.get("out") or "")[:200]: mm.append(f"step {k} out {(s.get('out') or '')[:80]!r} vs {(t.get('out') or '')[:80]!r}")
    for key in ("state_hash", "won", "rationale", "end_reason"):
        if a.get(key) != b.get(key): mm.append(f"{key} {str(a.get(key))[:120]!r} vs {str(b.get(key))[:120]!r}")
    return mm


def _episodes(res, idx=None):
    keys = ("won", "rationale", "state_hash", "end_reason", "traj", "games")
    n = len(res["games"])
    return [{k[:-1] if k == "games" else k: res[k][i] for k in keys} for i in (idx if idx is not None else range(n))]


def selftest(result_path, n=10, twice=False, workers=4):
    R = json.load(open(result_path, encoding="utf-8")); crashed = R.get("crashed") or [None] * len(R["games"])
    idx = [i for i in range(len(R["games"])) if not crashed[i]][:n]; tasks = [R["games"][i] for i in idx]
    replay = {R["games"][i]: replay_items(R["traj"][i]) for i in idx}
    patch = R.get("patch") if R.get("patch") not in (None, "none") and os.path.exists(R.get("patch")) else "none"
    if patch == "none" and R.get("patch") not in (None, "none"): print(f"selftest: patch {R.get('patch')} not found; setup code is not re-run", flush=True)
    over = {"max_steps": R["max_steps"], "gen_seconds": R["gen_seconds"]}
    A = run_eval(patch, R["seed"], f"{R['tag']}_selftestA", workers=workers, replay_only=True, tasks=tasks, replay=replay, hints={}, cfg_over=over, write=False)
    if twice:
        B = run_eval(patch, R["seed"], f"{R['tag']}_selftestB", workers=workers, replay_only=True, tasks=tasks, replay=replay, hints={}, cfg_over=over, write=False)
        ref, new = _episodes(A), _episodes(B)
    else: ref, new = _episodes(R, idx), _episodes(A)
    eps = []
    for a, b in zip(ref, new):
        mm = compare_eps(a, b, a["traj"], b["traj"]); eps.append({"task": a["game"], "ok": not mm, "n_steps": len(a["traj"]), "mismatches": mm[:20]})
    out = {"result": result_path, "tag": R["tag"], "n": len(eps), "twice": twice, "ok": all(e["ok"] for e in eps), "n_mismatch": sum(not e["ok"] for e in eps),
           "episodes": eps, "finished": time.strftime("%Y-%m-%d %H:%M")}
    d = os.path.join(_cfg()["out"], "results"); os.makedirs(d, exist_ok=True); path = os.path.join(d, f"selftest_{R['tag']}.json")
    with open(path, "w", encoding="utf-8") as f: json.dump(out, f, indent=1)
    print(f"selftest {R['tag']}: {len(eps) - out['n_mismatch']}/{len(eps)} episodes identical{' (two replays)' if twice else ''} -> {path}", flush=True)
    for e in eps:
        if not e["ok"]: print(f"  MISMATCH {e['task']}: {e['mismatches'][:3]}", flush=True)
    return out


def _reexec():
    """ARE's App.set_seed uses hash(): restart with PYTHONHASHSEED=0 unless already set (G2_NO_REEXEC=1 for local tests)."""
    if os.environ.get("PYTHONHASHSEED") == "0" or os.environ.get("G2_NO_REEXEC") == "1": return
    env = {**os.environ, "PYTHONHASHSEED": "0"}; argv = [sys.executable, os.path.abspath(__file__)] + sys.argv[1:]
    if os.name == "posix": os.execve(sys.executable, argv, env)
    sys.exit(subprocess.call(argv, env=env))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["eval", "selftest"]); ap.add_argument("--patch", default="none"); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tag", default="G2_F0"); ap.add_argument("--n-games", type=int, default=None); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--replay-only", action="store_true"); ap.add_argument("--result"); ap.add_argument("--n", type=int, default=10); ap.add_argument("--twice", action="store_true")
    a = ap.parse_args(); _reexec()
    if a.cmd == "eval": run_eval(a.patch, a.seed, a.tag, a.n_games, a.workers, replay_only=a.replay_only)
    else: sys.exit(0 if selftest(a.result, a.n, a.twice, a.workers)["ok"] else 1)


if __name__ == "__main__":
    main()
