#!/usr/bin/env python3
"""BENCHMARK OPPORTUNITY SEARCH — ALFWorld natural-candidate screen (2026-09-08). Guard 'bos_alfworld' $30 hard cap.
Backbone FROZEN: openrouter qwen/qwen3-30b-a3b-instruct-2507 (non-thinking instruct; $0.048/$0.193 per M).
F0 = the released SEED prompt-agent harness (ALFWORLD_TEMPLATE, history 5, <think><action> format, temperature 0.4,
max 50 steps, fallback 'look') on the FIXED 134-game unseen manifest. Candidates = executable-hook patches (see
HARNESS_API_DOC) proposed by gpt-4o from F0's failure profile. Every arm x seed is one full pass over the same 134 games.
Usage: eval --patch P|none --seed S --tag T | propose | summarize"""
import argparse, ast, json, os, re, sys, time, hashlib, urllib.request, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
SEED_ROOT = "/home/ymeng3/llm_agent_opd/external/SEED"; sys.path.insert(0, SEED_ROOT); sys.path.insert(0, f"{SEED_ROOT}/scripts/sft/_common")
sys.path.insert(0, "/net/scratch/ymeng3/metaharness_runs/level4")
OUT = "/net/scratch/ymeng3/bos_alfworld"; MANIFEST = os.environ.get("BOS_MANIFEST", f"{OUT}/manifests/unseen_shard_000.txt")  # closed-loop: env override, default unchanged
MODEL = os.environ.get("BOS_MODEL", "qwen/qwen3-30b-a3b-instruct-2507"); PRICE_IN, PRICE_OUT = float(os.environ.get("BOS_PRICE_IN", "0.130e-6")), float(os.environ.get("BOS_PRICE_OUT", "0.520e-6"))  # PINNED provider Alibaba rates (corrected 2026-09-09; 0.048/0.193 was StreamLake, the cheapest row)
KEY = os.environ.get("OPENROUTER_API_KEY") or (open(os.path.expanduser("~/.config/openrouter/key")).read().strip() if os.path.exists(os.path.expanduser("~/.config/openrouter/key")) else "")
from finalB_guard import SpendGuard
GUARD = SpendGuard("bos_alfworld", float(os.environ.get("BOS_GUARD_USD", "30.0")), f"{OUT}/guard_state.json")  # raised 30->36 (user-authorized 2026-09-08; see registry)
HOOKS = ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback")
HARNESS_API_DOC = """HARNESS HOOK API (ALFWorld text agent). A patch is a Python module that may define any subset of:
  HISTORY_LENGTH: int in [0, 20]            # how many previous (observation, action) pairs the prompt shows (default 5)
  TEMPERATURE: float in [0.0, 1.0]          # sampling temperature (default 0.4)
  def format_prompt(prompt: str, state: dict) -> str
      # prompt = the default full prompt (task, step count, recent history, current observation, admissible actions,
      # and the instruction to answer as <think>...</think><action>...</action>). Return the prompt to send.
      # state = a per-episode dict you own (persisted across steps; starts as {}).
  def parse_action(response: str, admissible: list[str], state: dict) -> str
      # Return the action string to execute (should be one of `admissible`, lowercase). Default: text inside <action></action>.
  def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None
      # Called when `action` is NOT admissible (attempt = 1, 2). Return None to accept the invalid action, or a dict with
      # optional keys {"extra_instruction": str appended to the prompt, "temperature": float} to re-query the model.
  def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None
      # Called after each executed step; mutate `state` (e.g. notes, visited receptacles, loop detection).
  def choose_fallback(admissible: list[str], state: dict) -> str
      # Called when the final action is still not admissible; return an admissible action (default: 'look').
Only the standard library modules re, json, math, random, collections, itertools, string may be imported (NOT difflib, os, sys).
No I/O, no network, no eval/exec. STRICT VALIDATOR RULES: the ONLY top-level `def` names allowed are the five hook names above;
any other top-level def (e.g. a helper) makes the whole patch INVALID. Put helpers as lambdas or as nested functions INSIDE a
hook. Module-level constants other than HISTORY_LENGTH / TEMPERATURE are allowed. The environment, task set, scoring, and the LLM
backbone cannot be changed."""
ALLOWED_IMPORTS = {"re", "json", "math", "random", "collections", "itertools", "string"}
FORBIDDEN = {"open", "exec", "eval", "__import__", "compile", "globals", "locals", "getattr", "setattr", "input", "breakpoint"}

def validate_patch(src):
    try: tree = ast.parse(src)
    except SyntaxError as e: return False, f"syntax: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in ALLOWED_IMPORTS for n in names): return False, f"import not allowed: {names}"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN: return False, f"forbidden name {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"): return False, "dunder attribute"
    top = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not top and not any(isinstance(n, ast.Assign) for n in tree.body): return False, "no hook defined"
    for fn in top:
        if fn.name not in HOOKS: return False, f"unknown hook {fn.name}"
    return True, "ok"

def load_patch(path):
    if path in (None, "none"): return {}
    src = open(path).read(); ok, why = validate_patch(src); assert ok, why
    ns = {}; exec(compile(src, path, "exec"), ns)  # validated above
    return ns

def default_parse(response):
    m = re.search(r"<action>(.*?)</action>", response, re.S | re.I)
    return m.group(1).strip().lower() if m else response.strip().lower()[-30:]

class Backbone:
    def __init__(self, temperature):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get("BOS_API_KEY", KEY), base_url=os.environ.get("BOS_BASE_URL", "https://openrouter.ai/api/v1"), timeout=60, max_retries=0)  # backbone only; gpt4o() proposer unaffected
        self.extra = ({"provider": {"order": [os.environ["BOS_PROVIDER"]], "allow_fallbacks": os.environ.get("BOS_FALLBACKS", "1") == "1"}} if os.environ.get("BOS_PROVIDER") else None)
        self.sampling = {}  # explicit decoding protocol; default = send nothing (unchanged behaviour)
        if os.environ.get("BOS_TOP_P"): self.sampling["top_p"] = float(os.environ["BOS_TOP_P"])
        if os.environ.get("BOS_TOP_K"): self.extra = {**(self.extra or {}), "top_k": int(os.environ["BOS_TOP_K"])}
        if os.environ.get("BOS_REASONING_OFF") == "1":   # regime tests on thinking-capable models: harness protocol is NON-thinking
            self.extra = {**(self.extra or {}), "reasoning": {"enabled": False}}
        self.err_types = {}
        self.temperature = temperature; self.lock = threading.Lock(); self.tok = [0, 0]; self.calls = 0; self.errors = 0
    def call(self, prompt, temperature=None):
        last = None
        for attempt in range(5):
            try:
                r = self.client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}],
                                                        temperature=self.temperature if temperature is None else temperature, max_tokens=int(os.environ.get("BOS_MAX_TOKENS", "512")), n=1, extra_body=self.extra, **self.sampling)
                u = r.usage
                with self.lock: self.tok[0] += u.prompt_tokens; self.tok[1] += u.completion_tokens; self.calls += 1
                return (r.choices[0].message.content or "").strip(), None
            except Exception as e:
                if "402" in str(e) or "Insufficient credit" in str(e): raise SystemExit(f"FATAL: HTTP 402 credit exhaustion; pass aborted, no fallback actions ({str(e)[:80]})")
                last = e; k = f"{type(e).__name__}:{str(e)[:60]}"
                with self.lock: self.err_types[k] = self.err_types.get(k, 0) + 1
                time.sleep(min(30, 2.0 * (2 ** attempt)))
        with self.lock: self.errors += 1
        return "", f"{type(last).__name__}: {last}"
    def cost(self): return self.tok[0] * PRICE_IN + self.tok[1] * PRICE_OUT

def run_eval(patch_path, seed, tag, n_games=None, workers=16):
    from pipeline import build_manager
    hooks = load_patch(patch_path); H = int(hooks.get("HISTORY_LENGTH", 5)); T = float(hooks.get("TEMPERATURE", 0.4))
    assert 0 <= H <= 20 and 0.0 <= T <= 1.0
    games = [l.strip() for l in open(MANIFEST) if l.strip()][: (n_games or 10 ** 9)]
    REPLAY = json.load(open(os.environ["BOS_REPLAY"])) if os.environ.get("BOS_REPLAY") else {}   # Probe L (2026-09-23): {game: [prefix actions]} replayed without LLM calls; env is deterministic
    GUARD.baseline(); GUARD.check()
    mgr = build_manager(game_files=games, alf_config_path=f"{SEED_ROOT}/agent_system/environments/env_package/alfworld/configs/config_tw.yaml", seed=seed, history_length=H)
    bb = Backbone(T); N = len(games)
    obs, infos = mgr.reset({}); games_actual = [str((infos[i] or {}).get("extra.gamefile", "")) for i in range(N)]   # actual gamefile per slot (env may permute by seed); record only
    done = [False] * N; won = [False] * N; steps = [0] * N; invalid = [0] * N; retries = [0] * N
    state = [{} for _ in range(N)]; traj = [[] for _ in range(N)]; stepinfo = {}
    HINTS = json.load(open(os.environ["BOS_HINTS"])) if os.environ.get("BOS_HINTS") else {}   # failure-driven alternatives (2026-09-25): {actual gamefile: strategy text}; patches may read state["_hint"]
    for i in range(N):
        h = HINTS.get(games_actual[i]) or HINTS.get(games[i])
        if h: state[i]["_hint"] = h   # per-step trigger log (2026-09-23; record only)
    fx = {"prompt_changed": 0, "action_changed_by_parse": 0, "retry_calls": 0, "fallback_used": 0, "memory_calls": 0, "admissible": 0, "steps": 0}
    fp = hooks.get("format_prompt"); pa = hooks.get("parse_action"); rp = hooks.get("retry_policy"); mu = hooks.get("memory_update"); cf = hooks.get("choose_fallback")
    def act(i):
        adm = [a.lower() for a in mgr.envs.get_admissible_commands[i] if a != "help"]
        prompt = obs["text"][i]; prompt0 = prompt
        try:
            if fp: prompt = fp(prompt, state[i])
        except Exception: pass
        if prompt != prompt0: fx["prompt_changed"] += 1
        resp, err = bb.call(prompt); action = None; si = {"pc": int(prompt != prompt0), "calls": 1}
        if os.environ.get("BOS_LOG_RAW") == "1": si["raw0"] = (resp or "")[-300:]
        try: action = pa(resp, adm, state[i]) if pa else default_parse(resp)
        except Exception: action = default_parse(resp)
        if pa and action != default_parse(resp): fx["action_changed_by_parse"] += 1
        si["parse_chg"] = int(bool(pa) and action != default_parse(resp)); si["a0"] = (action or "")[:60]; si["a0_adm"] = int(action in adm)
        attempt = 0
        while rp and action not in adm and attempt < 2:
            attempt += 1
            try: pol = rp(attempt, resp, action, adm, state[i])
            except Exception: pol = None
            if not pol: break
            retries[i] += 1; fx["retry_calls"] += 1; si["calls"] += 1
            resp, err = bb.call(prompt + ("\n\n" + pol.get("extra_instruction", "") if pol.get("extra_instruction") else ""), pol.get("temperature"))
            try: action = pa(resp, adm, state[i]) if pa else default_parse(resp)
            except Exception: action = default_parse(resp)
        if action not in adm and cf:
            try:
                fb = cf(adm, state[i]); action = fb if fb in adm else action; fx["fallback_used"] += 1; si["fb"] = 1
            except Exception: pass
        fx["steps"] += 1; fx["admissible"] += int(action in adm); state[i]["_last_admissible"] = action in adm
        si["retry_n"] = attempt; si["retry_chg"] = int(attempt > 0 and (action or "") != si.get("a0")); si.setdefault("fb", 0); stepinfo[i] = si
        if not hooks: return i, resp if resp else "<think>api error</think><action>look</action>", resp   # F0: raw response to the env projection, as released
        return i, f"<think>.</think><action>{action}</action>", resp
    for step in range(50):
        GUARD.check(); active = [i for i in range(N) if not done[i]]
        if not active: break
        actions = ["<think>The episode is done.</think><action>look</action>"] * N; raw = [""] * N
        live = []
        for i in active:                                    # replay prefix actions (no LLM, no parse/retry/fallback); format_prompt still runs for its state writes
            pre = REPLAY.get(games_actual[i]) if REPLAY.get(games_actual[i]) is not None else REPLAY.get(games[i])   # key by the ACTUAL gamefile in this slot (env permutes per seed)
            if pre is not None and step < len(pre):
                try:
                    if fp: fp(obs["text"][i], state[i])
                except Exception: pass
                actions[i] = f"<think>.</think><action>{pre[step]}</action>"; raw[i] = ""; stepinfo[i] = {"replayed": 1}; fx["steps"] += 1; state[i]["_last_admissible"] = True
            elif os.environ.get("BOS_REPLAY_ONLY") == "1" and pre is not None: actions[i] = "<think>.</think><action>look</action>"; raw[i] = ""; done[i] = True; stepinfo[i] = {"replayed": 0, "stopped": 1}
            else: live.append(i)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            for fut in as_completed([ex.submit(act, i) for i in live]):
                i, a, r = fut.result(); actions[i] = a; raw[i] = r
        prev_anchor = list(obs["anchor"]); nobs, rewards, dones, infos = mgr.step(actions)
        print(f"  step {step}: active {len(active)} won so far {sum(won)} calls {bb.calls} errors {bb.errors} cost ${bb.cost():.3f} t={time.strftime('%H:%M:%S')} err_types={dict(list(bb.err_types.items())[:3])}", flush=True)
        for i in active:
            steps[i] += 1; invalid[i] += int(not bool(infos[i].get("is_action_valid", 1)))
            traj[i].append({"step": step, "action": actions[i][-120:], "valid": bool(infos[i].get("is_action_valid", 1)), "admissible": bool(state[i].get("_last_admissible", False)), "obs": str(nobs["anchor"][i])[:160], **stepinfo.get(i, {})})
            if mu:
                try: mu(state[i], prev_anchor[i], actions[i], nobs["anchor"][i]); fx["memory_calls"] += 1
                except Exception: pass
            if dones[i]: done[i] = True; won[i] = bool(infos[i].get("won", False))
        obs = nobs
    task_types = [os.path.basename(os.path.dirname(os.path.dirname(g))).split("-")[0] for g in games]
    res = {"tag": tag, "patch": patch_path, "manifest": MANIFEST, "seed": seed, "model": MODEL, "history_length": H, "temperature": T, "n_games": N,
           "success_rate": sum(won) / N, "won": won, "steps": steps, "invalid": invalid, "retries": retries, "task_types": task_types, "games_actual": games_actual,
           "games": games, "tokens_in": bb.tok[0], "tokens_out": bb.tok[1], "calls": bb.calls, "api_errors": bb.errors, "error_types": bb.err_types, "cost_usd": bb.cost(), "hook_effects": fx,
           "traj": traj, "finished": time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(f"{OUT}/results", exist_ok=True); json.dump(res, open(f"{OUT}/results/{tag}_seed{seed}.json", "w"))
    print(f"{tag} seed{seed}: success {res['success_rate']:.3f} ({sum(won)}/{N}) mean steps {sum(steps)/N:.1f} invalid {sum(invalid)} admissible-rate {fx['admissible']/max(1,fx['steps']):.2f} retries {sum(retries)} hook_effects {fx} cost ${bb.cost():.3f} api_errors {bb.errors} guard spent ${GUARD.spent():.2f}", flush=True)

def f0_profile():
    import glob, collections
    fs = sorted(glob.glob(f"{OUT}/results/F0_seed*.json")); assert fs, "run F0 first"
    R = [json.load(open(f)) for f in fs]; fam = collections.defaultdict(list); loops = 0; maxed = 0; inv = 0; n = 0
    for r in R:
        for i in range(r["n_games"]):
            fam[r["task_types"][i]].append(r["won"][i]); n += 1; inv += r["invalid"][i]; maxed += int(r["steps"][i] >= 50 and not r["won"][i])
            acts = [t["action"] for t in r["traj"][i]]; loops += int(any(acts[j] == acts[j - 1] == acts[j - 2] for j in range(2, len(acts))))
    return {"seeds": len(R), "success_rate": sum(x["success_rate"] for x in R) / len(R), "success_by_task_family": {k: round(sum(v) / len(v), 3) for k, v in fam.items()},
            "episodes": n, "invalid_actions_per_episode": round(inv / n, 2), "fraction_episodes_hitting_max_steps": round(maxed / n, 3),
            "fraction_episodes_with_3x_repeated_action": round(loops / n, 3), "mean_steps": round(sum(sum(x["steps"]) for x in R) / n, 1)}

def gpt4o(messages, temperature=1.0, max_tokens=1400):
    GUARD.check()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                                 data=json.dumps({"model": "openai/gpt-4o", "messages": messages, "temperature": temperature, "max_tokens": max_tokens}).encode())
    with urllib.request.urlopen(req, timeout=180) as r: return json.loads(r.read().decode())["choices"][0]["message"]["content"]

PROPOSER_SYS = ("You are a coding agent improving an LLM text-agent harness for embodied household tasks (ALFWorld). You may only change "
                "the harness through the hook API given below; the model, environment and scoring are fixed. Output exactly:\nNAME: <short_snake_case>\n"
                "```python\n<patch module>\n```")

def propose(K=10):
    prof = f0_profile(); cands = []; log = []; attempts = 0; os.makedirs(f"{OUT}/patches", exist_ok=True)
    while len(cands) < K and attempts < 2 * K:
        attempts += 1
        user = (f"[proposal attempt {attempts}]\n{HARNESS_API_DOC}\n\nBASELINE (F0) PROFILE on the 134 unseen games:\n{json.dumps(prof)}\n\n"
                f"DEFAULT PROMPT TEMPLATE the model sees each step:\n{open(f'{SEED_ROOT}/agent_system/environments/prompts/alfworld.py').read().split('ALFWORLD_TEMPLATE = \"\"\"')[1].split('\"\"\"')[0]}\n\n"
                f"Names of your earlier proposals (do not repeat their idea): {json.dumps([c['name'] for c in cands])}\n\nPropose ONE new patch.")
        resp = gpt4o([{"role": "system", "content": PROPOSER_SYS}, {"role": "user", "content": user}])
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp)
        name = (nm.group(1)[:40] if nm else f"unnamed{attempts}"); src = m.group(1).strip() if m else None
        ok, why = (validate_patch(src) if src else (False, "no code"))
        log.append({"attempt": attempts, "name": name, "ok": ok, "why": why, "resp": resp})
        if not ok: continue
        try: load_patch_src = {}; exec(compile(src, name, "exec"), load_patch_src)
        except Exception as e: log[-1]["why"] = f"exec: {e}"; continue
        pid = f"N{len(cands)+1:02d}_{name}"; open(f"{OUT}/patches/{pid}.py", "w").write(src); cands.append({"name": pid, "src": src})
    frozen = {"created": time.strftime("%Y-%m-%d %H:%M"), "backbone": MODEL, "proposer": "openai/gpt-4o T=1.0", "f0_profile": prof, "candidates": [c["name"] for c in cands],
              "candidates_sha": hashlib.sha256(json.dumps([c["src"] for c in cands]).encode()).hexdigest()[:16], "manifest_sha": hashlib.sha256(open(MANIFEST, "rb").read()).hexdigest()[:16],
              "seeds": [1, 2, 3], "proposer_log": log, "spent_after_propose": round(GUARD.spent(), 3)}
    json.dump(frozen, open(f"{OUT}/bos_alfworld_frozen.json", "w"), indent=1)
    print(f"FREEZE ECHO: {len(cands)} candidates sha {frozen['candidates_sha']} manifest sha {frozen['manifest_sha']} backbone {MODEL} seeds {frozen['seeds']} spent ${frozen['spent_after_propose']}")
    for c in cands: print("  ", c["name"])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--patch", default="none"); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tag", default="F0"); ap.add_argument("--n-games", type=int, default=None); ap.add_argument("--workers", type=int, default=16); a = ap.parse_args()
    if a.cmd == "eval": run_eval(a.patch, a.seed, a.tag, a.n_games, a.workers)
    elif a.cmd == "propose": propose()
