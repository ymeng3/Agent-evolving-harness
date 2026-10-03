"""LINE 3 v3 (2026-09-28): two-layer harness. Capability {Planning, Memory, ToolUse, Recovery, Verification} x Implementation
{Prompt, State, Code, ControlFlow}. A patch is a Python module with EDITS = [ {id, capability, impl, trigger, depends}, ... ] and
functions <id>_setup() -> sandbox code str | <id>_pre_call(prompt, state) -> prompt | <id>_post_parse(code, state) -> code |
<id>_post_exec(code, out, state) -> None | <id>_pre_complete(code, state) -> code (only when code calls complete_task).
Control points: setup once before step 0; pre_call before every LLM call; post_parse after code extraction; post_exec after
execution; pre_complete before executing a cell that calls complete_task. BOS_EDITS_OFF="e2,e4" disables edits (dependency-closed).
Legacy 5-hook patches (format_prompt etc.) still work through the same points."""

import os, sys, json, re, time, argparse, threading
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
os.environ.setdefault("APPWORLD_ROOT", "/net/scratch/ymeng3/appworld_v2"); os.environ.setdefault("TMPDIR", os.environ.get("BOS_TMPDIR", "/net/scratch/ymeng3/pip_tmp"))
sys.path.insert(0, os.environ.get("BOS_ALF_DIR", "/net/scratch/ymeng3/bos_alfworld")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "alfworld")); import bos_alfworld as A
OUT = os.environ.get("BOS_OUT", os.path.dirname(os.path.abspath(__file__))); TASKS = json.load(open(os.environ.get("BOS_TASKS", f"{OUT}/tasks50.json")))
INSTR = open(os.environ.get("BOS_AW_INSTR", "/net/scratch/ymeng3/appworld_repo/experiments/prompts/react_code_agent/instructions.txt")).read()
MAX_STEPS = int(os.environ.get("BOS_AW_STEPS", "30"))
REPLAY = json.load(open(os.environ["BOS_REPLAY"])) if os.environ.get("BOS_REPLAY") else {}
HINTS = json.load(open(os.environ["BOS_HINTS"])) if os.environ.get("BOS_HINTS") else {}
def demo_messages(sup):
    txt = INSTR.replace("{{ main_user.first_name }}", sup.first_name).replace("{{ main_user.last_name }}", sup.last_name).replace("{{ main_user.email }}", sup.email).replace("{{ main_user.phone_number }}", sup.phone_number)
    msgs = []; role = None; buf = []
    for line in txt.split("\n"):
        if line.strip() in ("USER:", "ASSISTANT:"):
            if role: msgs.append({"role": role, "content": "\n".join(buf).strip()})
            role = "user" if line.strip() == "USER:" else "assistant"; buf = []
        else: buf.append(line)
    if role: msgs.append({"role": role, "content": "\n".join(buf).strip()})
    return msgs
PARSE_UNCLOSED = os.environ.get("BOS_PARSE_UNCLOSED", "0") == "1"   # 2026-09-29: 10-30% of 27B replies open a code fence and never close it; default parser then returns "" and the step silently runs the default code
def extract_code(resp):
    m = re.search(r"```python\s*(.*?)```", resp, re.S) or re.search(r"```\s*(.*?)```", resp, re.S)
    if m: return m.group(1).strip()
    if PARSE_UNCLOSED:   # no closed pair -> exactly one opening fence; take everything after it
        m = re.search(r"```(?:python)?[ \t]*\n(.*)$", resp, re.S)
        if m: return m.group(1).strip()
    return ""
# 2026-10-03 HARNESS_V2 (diagnosis of 93 failed discovery attempts: silent fallback / truncated / placeholder code cost up to 21 cells per
# episode; win rate 0.57 -> 0.00 as such cells go 0 -> 6+). Opt-in so the old baseline stays reproducible.
HARNESS_V2 = os.environ.get("BOS_HARNESS_V2", "0") == "1"; FREE_RETRIES_STEP, FREE_RETRIES_EP = 3, 12
def extract_code_v2(resp):
    """the LAST closed ```python block (the final answer comes after any reasoning drafts); else the last closed ``` block; else the
    text after a final unclosed fence (usually truncated, so validate_code will reject it unless it happens to be complete)."""
    for pat in (r"```python[ \t]*\n(.*?)```", r"```[a-z]*[ \t]*\n(.*?)```"):
        blocks = re.findall(pat, resp, re.S)
        if blocks: return blocks[-1].strip()
    if resp.count("```") % 2 == 1:
        m = re.search(r"```(?:python)?[ \t]*\n((?:(?!```).)*)$", resp, re.S)
        if m: return m.group(1).strip()
    return ""
def validate_code(code):
    """-> reason string if the code must not be executed, else ''."""
    if not code.strip(): return "your reply contained no ```python code block"
    try: tree = _ast.parse(code)
    except SyntaxError as e: return f"the code block is incomplete or not valid Python (SyntaxError: {e.msg}, line {e.lineno}); the reply was probably cut off"
    if any(isinstance(n, _ast.Constant) and n.value is Ellipsis for n in _ast.walk(tree)): return "the code contains a '...' placeholder instead of real values"
    return ""
def out_cap(code): return 8000 if (HARNESS_V2 and "api_docs" in code) else 3000   # full API lists were cut at 3000 chars and re-listed 1-6 times
_PLAY = None; _TASKS = None
def _call(i):
    try: return _PLAY(i)
    except Exception as e:   # 2026-10-01: one task's exception used to abort the whole ProcessPool pass (43 min lost); record it as a crashed failure instead
        return i, {"bb": [0, 0, 0, 0], "task": _TASKS[i], "won": False, "G": None, "harm_fail": 0, "steps": 0, "traj": [], "crashed": f"{type(e).__name__}: {str(e)[:200]}"}
import ast as _ast
ALLOWED_POINTS = ("setup", "pre_call", "post_parse", "post_exec", "pre_complete")
def load_v3(path):
    """validate + load a two-layer patch; returns (edits_meta, funcs_by_point) with OFF edits (dependency-closed) removed."""
    src = open(path).read(); tree = _ast.parse(src)
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Import, _ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, _ast.Import) else [(node.module or "").split(".")[0]]
            assert all(n in A.ALLOWED_IMPORTS for n in names), f"import not allowed: {names}"
        if isinstance(node, _ast.Name) and node.id in A.FORBIDDEN: raise AssertionError(f"forbidden name {node.id}")
    ns = {}; exec(compile(src, path, "exec"), ns)
    edits = ns.get("EDITS") or []
    ids = [e["id"] for e in edits]; assert len(ids) == len(set(ids)), "duplicate edit ids"
    for fn in [n for n in tree.body if isinstance(n, _ast.FunctionDef)]:
        if fn.name in A.HOOKS: continue
        pid, _, pt = fn.name.rpartition("_"); pid2, _, pt2 = fn.name.partition("_")
        assert (pt in ALLOWED_POINTS and pid in ids) or fn.name.split("_", 1)[1] in ("pre_call", "post_parse", "post_exec", "pre_complete", "setup") and fn.name.split("_", 1)[0] in ids, f"unknown function {fn.name}"
    off = set(x for x in os.environ.get("BOS_EDITS_OFF", "").split(",") if x); changed = True
    while changed:
        changed = False
        for e in edits:
            if e["id"] not in off and any(d in off for d in e.get("depends", [])): off.add(e["id"]); changed = True
    active = [e for e in edits if e["id"] not in off]
    funcs = {p: [] for p in ALLOWED_POINTS}
    for e in active:
        for p in ALLOWED_POINTS:
            f = ns.get(f"{e['id']}_{p}")
            if f: funcs[p].append((e["id"], f))
    legacy = {k: ns[k] for k in A.HOOKS if k in ns}; consts = {k: ns[k] for k in ("HISTORY_LENGTH", "TEMPERATURE", "SETUP_CODE") if k in ns}
    return active, off, funcs, legacy, consts
def run_eval(patch_path, seed, tag, n_games=None, workers=4):
    from appworld import AppWorld
    hooks = {}; V3 = None
    if patch_path not in (None, "none"):
        src = open(patch_path).read()
        if "EDITS" in src:
            active, off, funcs, legacy, consts = load_v3(patch_path); V3 = funcs; hooks = {**legacy, **consts}
            print(f"v3 patch: active edits {[e['id'] for e in active]} off {sorted(off)}", flush=True)
        else: hooks = A.load_patch(patch_path)
    fp, pa, rp, mu, cf = (hooks.get(k) for k in ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback"))
    H = int(hooks.get("HISTORY_LENGTH", 20)); T = float(hooks.get("TEMPERATURE", 0.4)); tasks = TASKS[: (n_games or 10**9)]
    def play(i):
        bb = A.Backbone(T); tid = tasks[i]; state = {}; traj = []; free_used = [0]; steps = 0; success = False; gp = gf = 0; pre = REPLAY.get(tid) or []
        if HINTS.get(tid): state['_hint'] = HINTS[tid]
        with AppWorld(task_id=tid, experiment_name=f"line3_{tag}_s{seed}", random_seed=seed) as world:
            base = demo_messages(world.task.supervisor)
            # the demo ends with the example task; replace the last USER turn's task line with the real task
            task_msg = f"My name is: {world.task.supervisor.first_name} {world.task.supervisor.last_name}. My personal email is {world.task.supervisor.email} and phone number is {world.task.supervisor.phone_number}.\nTask: {world.task.instruction}"
            hist = []   # list of (assistant_text, user_output)
            setup_codes = [str(hooks["SETUP_CODE"])] if hooks.get("SETUP_CODE") else []
            for eid, f in (V3["setup"] if V3 else []):   # 2026-10-03: a raising setup hook used to crash every task of the pass
                try: sc = f(); setup_codes += [sc] if isinstance(sc, str) and sc.strip() else []
                except Exception as e: state.setdefault("_edit_err", []).append(f"{eid}:setup:{str(e)[:40]}")
            for sc in setup_codes:
                try: state["_setup_out"] = world.execute(sc)[:300]
                except Exception as e: state["_setup_out"] = f"setup error {e}"[:300]
            for step in range(MAX_STEPS):
                A.GUARD.check()
                turns = hist[-H:]; msgs = base[:-1] + [{"role": "user", "content": base[-1]["content"].split("Task:")[0] + task_msg.split("\n")[-1] if False else task_msg}]
                for a_txt, u_out in turns: msgs += [{"role": "assistant", "content": a_txt}, {"role": "user", "content": u_out}]
                if step < len(pre):   # exact replay of a logged prefix: no LLM call, same code, environment is deterministic
                    code = pre[step]; out = world.execute(code); err = out.startswith("Execution failed")
                    try:
                        if mu: mu(state, hist[-1][1] if hist else "", code, out)
                    except Exception: pass
                    ev = world.evaluate().to_dict(); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail")
                    traj.append({"step": step, "code": code, "out": out[:200], "exec_error": int(err), "gp": gp, "gf": gf, "replayed": 1})
                    hist.append(("```python\n" + code + "\n```", "Output:\n```\n" + out[:3000] + "\n```")); steps += 1
                    if world.task_completed(): break
                    continue
                prompt0 = msgs[-1]["content"]; prompt = prompt0; si = {"pc": 0, "calls": 1}
                try:
                    if fp: prompt = fp(prompt, state)
                except Exception: pass
                if V3:
                    for eid, f in V3["pre_call"]:
                        try: p2 = f(prompt, state); prompt = p2 if isinstance(p2, str) and p2.strip() else prompt   # 2026-10-03: a hook returning None used to send content=None
                        except Exception as e: si.setdefault("edit_err", []).append(f"{eid}:pre_call:{str(e)[:40]}")
                si["pc"] = int(prompt != prompt0); msgs[-1] = {"role": "user", "content": prompt}
                resp = ""
                r = None; last = None
                for att in range(6):   # 2026-09-28: retry with backoff; stale keep-alive connections through the ssh forward were surfacing as 'Connection error.' once per step with NO retry
                    try:
                        r = bb.client.chat.completions.create(model=A.MODEL, messages=msgs, temperature=T, max_tokens=int(os.environ.get("BOS_MAX_TOKENS", "1024")), n=1, extra_body=bb.extra, **bb.sampling); break
                    except Exception as e:
                        last = e; si["api_retries"] = att + 1
                        if "402" in str(e): raise
                        try: from openai import OpenAI; bb.client = OpenAI(api_key=os.environ.get("BOS_API_KEY", A.KEY), base_url=os.environ.get("BOS_BASE_URL", "https://openrouter.ai/api/v1"), timeout=float(os.environ.get("BOS_TIMEOUT", "60")), max_retries=0)
                        except Exception: pass
                        time.sleep(min(30, 2 * (2 ** att)))
                if r is not None:
                    resp = (r.choices[0].message.content or ""); bb.tok[0] += r.usage.prompt_tokens; bb.tok[1] += r.usage.completion_tokens; bb.calls += 1
                else:
                    bb.errors += 1; si["api_error"] = str(last)[:80]
                ex_ = extract_code_v2 if HARNESS_V2 else extract_code
                try: code = pa(resp, [], state) if pa else ex_(resp)
                except Exception: code = ex_(resp)
                si["parse_chg"] = int(bool(pa) and code != ex_(resp)); si["a0"] = ex_(resp)[:80]; si["a0_adm"] = int(bool(ex_(resp))); si["unclosed"] = int(resp.count("```") % 2 == 1)
                if HARNESS_V2:   # never execute a missing / truncated / placeholder block: say why and ask again, without spending a cell
                    why = validate_code(code); n_free = 0
                    while why and n_free < FREE_RETRIES_STEP and free_used[0] < FREE_RETRIES_EP:
                        n_free += 1; free_used[0] += 1
                        fb_msg = (f"Nothing was executed: {why}. Your variables and all app state are unchanged and this did not use up a step. "
                                  f"Reply with ONE complete ```python code block now (keep any reasoning short).")
                        try:
                            r2 = bb.client.chat.completions.create(model=A.MODEL, messages=msgs + [{"role": "assistant", "content": resp[-4000:] or "(empty reply)"}, {"role": "user", "content": fb_msg}],
                                                                   temperature=T, max_tokens=int(os.environ.get("BOS_MAX_TOKENS", "1024")), n=1, extra_body=bb.extra, **bb.sampling)
                            resp = r2.choices[0].message.content or ""; bb.tok[0] += r2.usage.prompt_tokens; bb.tok[1] += r2.usage.completion_tokens; bb.calls += 1
                        except Exception as e:
                            si["api_error"] = str(e)[:80]; break
                        code = ex_(resp); why = validate_code(code)
                    si["free_retries"] = n_free
                    if why: code = ""; si["invalid_code"] = why[:80]
                attempt = 0
                while rp and not code and attempt < 2:
                    attempt += 1
                    try: pol = rp(attempt, resp, code, [], state)
                    except Exception: pol = None
                    if not pol: break
                    si["calls"] += 1
                    for att in range(4):
                        try:
                            r = bb.client.chat.completions.create(model=A.MODEL, messages=msgs + [{"role": "user", "content": pol.get("extra_instruction", "")}], temperature=pol.get("temperature", T), max_tokens=1024, n=1, extra_body=bb.extra, **bb.sampling)
                            resp = (r.choices[0].message.content or ""); bb.calls += 1; break
                        except Exception: time.sleep(2 * (2 ** att))
                    try: code = pa(resp, [], state) if pa else extract_code(resp)
                    except Exception: code = extract_code(resp)
                si["retry_n"] = attempt; si["retry_chg"] = int(attempt > 0 and bool(code)); si["fb"] = 0
                if not code and cf:
                    try: code = cf([], state) or ""; si["fb"] = int(bool(code))
                    except Exception: pass
                if not code and HARNESS_V2:   # free retries exhausted: spend the step, execute nothing, and say so
                    out = f"Nothing was executed this step: {si.get('invalid_code', 'no valid code block')}. Variables and app state are unchanged."
                    err = True; si["no_exec"] = 1
                    ev = world.evaluate().to_dict(); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail"); sf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_pass")
                    traj.append({"step": step, "code": "", "resp": resp[-600:], "out": out[:200], "exec_error": 1, "gp": gp, "gf": gf, "harm_fail": sf, **si})
                    hist.append((resp[-4000:] or "(empty reply)", "Output:\n```\n" + out + "\n```")); steps += 1
                    continue
                if not code: code = "print(apis.api_docs.show_app_descriptions())"; si["default_code"] = 1
                if V3:
                    for eid, f in V3["post_parse"]:
                        try: c2 = f(code, state); code = c2 if isinstance(c2, str) and c2.strip() else code
                        except Exception as e: si.setdefault("edit_err", []).append(f"{eid}:post_parse:{str(e)[:40]}")
                    if "complete_task" in code:
                        for eid, f in V3["pre_complete"]:
                            try: c2 = f(code, state); code = c2 if isinstance(c2, str) and c2.strip() else code
                            except Exception as e: si.setdefault("edit_err", []).append(f"{eid}:pre_complete:{str(e)[:40]}")
                si["code_final"] = code[:300]
                try: out = world.execute(code)
                except Exception as e: out = f"Execution failed. {type(e).__name__}: {str(e)[:300]}"; si["env_exc"] = 1   # 2026-10-01: e.g. an API called with `...` as an argument raises inside AppWorld's save_logs
                err = out.startswith("Execution failed")
                try:
                    if mu: mu(state, hist[-1][1] if hist else "", code, out)
                except Exception: pass
                if V3:
                    for eid, f in V3["post_exec"]:
                        try: f(code, out, state)
                        except Exception as e: si.setdefault("edit_err", []).append(f"{eid}:post_exec:{str(e)[:40]}")
                ev = world.evaluate().to_dict(); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail"); sf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_pass")
                traj.append({"step": step, "code": code, "resp": resp[-600:], "out": out[:200], "exec_error": int(err), "gp": gp, "gf": gf, "harm_fail": sf, **si})
                hist.append((resp if resp else "```python\n" + code + "\n```", "Output:\n```\n" + out[:out_cap(code)] + "\n```")); steps += 1
                if world.task_completed(): break
            ev = world.evaluate().to_dict(); success = bool(ev.get("success")); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail"); sf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_pass")
        return i, {"bb": [bb.calls, bb.errors, bb.tok[0], bb.tok[1]], "task": tid, "won": success, "G": (gp / (gp + gf) if gp + gf else None), "harm_fail": sf, "steps": steps, "traj": traj}
    global _PLAY, _TASKS; _PLAY = play; _TASKS = tasks; results = [None] * len(tasks)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context('fork')) as ex:
        for i, r in ex.map(_call, range(len(tasks))): results[i] = r
    class _B: pass
    bb = _B(); bb.calls = sum(r['bb'][0] for r in results); bb.errors = sum(r['bb'][1] for r in results); bb.tok = [sum(r['bb'][2] for r in results), sum(r['bb'][3] for r in results)]
    G = [r["G"] for r in results if r["G"] is not None]
    res = {"tag": tag, "patch": patch_path, "seed": seed, "model": A.MODEL, "history_length": H, "temperature": T, "parse_unclosed": PARSE_UNCLOSED, "harness_v2": HARNESS_V2, "max_tokens": int(os.environ.get("BOS_MAX_TOKENS", "1024")), "backbone_extra": A.Backbone(T).extra, "n_games": len(tasks), "success_rate": sum(r["won"] for r in results) / len(tasks), "mean_G": sum(G) / max(len(G), 1),
           "won": [r["won"] for r in results], "G": [r["G"] for r in results], "harm_fail": [r["harm_fail"] for r in results], "games": [r["task"] for r in results], "steps": [r["steps"] for r in results], "crashed": [r.get("crashed") for r in results], "traj": [r["traj"] for r in results],
           "calls": bb.calls, "api_errors": bb.errors, "tokens_in": bb.tok[0], "tokens_out": bb.tok[1], "finished": time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(f"{OUT}/results", exist_ok=True); json.dump(res, open(f"{OUT}/results/{tag}_seed{seed}.json", "w"))
    print(f"{tag} seed{seed}: success {res['success_rate']:.3f} mean_G {res['mean_G']:.2f} calls {bb.calls} api_errors {bb.errors}", flush=True)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--patch", default="none"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--tag", default="AW_F0"); ap.add_argument("--n-games", type=int, default=None); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(); run_eval(a.patch, a.seed, a.tag, a.n_games, a.workers)
