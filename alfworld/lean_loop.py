"""LEAN EVOLUTION LOOP (2026-09-26). Per round: propose K composite candidates (gpt-4o) -> paired test vs parent (train48, seed 1)
-> only candidates with >= parent+2 wins are decomposed -> OFF each changed unit (local units: replay-to-trigger branch; global:
adaptive 16/32/48) -> revert harmful units = lean candidate -> retest lean -> confirm best of {C, lean} on seed 2 -> commit.
Decisions by win counts (no CI gate). Env: LL_ARENA (alfworld), LL_BACKEND (local|api), LL_PARENT, LL_STATE, LL_ROUNDS, LL_K."""
import ast, json, os, re, sys, time, subprocess, collections
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag")
import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_alfworld"; H = "/net/scratch/ymeng3/bos_screens/hag"; LED = os.path.expanduser("~/agent_knowledge/validation_line/METHOD_REGISTRY.md")
ARENA = os.environ.get("LL_ARENA", "alfworld"); BACKEND = os.environ.get("LL_BACKEND", "local"); STATE = os.environ.get("LL_STATE", f"{R}/lean_state.json"); K = int(os.environ.get("LL_K", "4"))
MAN = os.environ.get("LL_MANIFEST", f"{R}/slices/train48.txt"); NG = int(os.environ.get("LL_NGAMES", "48")); AW = "/net/scratch/ymeng3/bos_appworld"; RES = AW if ARENA == "appworld" else R; PD = f"{RES}/patches_lean"; os.makedirs(PD, exist_ok=True)
HOOKS = set(A.HOOKS) | {"HISTORY_LENGTH", "TEMPERATURE"}; LOCAL = {"choose_fallback", "retry_policy", "parse_action"}
def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)
    with open(f"{RES}/lean_loop.log", "a") as f: f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
def S_load(): return json.load(open(STATE)) if os.path.exists(STATE) else {"round": 1, "parent": os.environ["LL_PARENT"], "history": [], "memory": []}
def S_save(S): json.dump(S, open(STATE, "w"), indent=1)
AW_API_DOC = """HARNESS HOOK API (AppWorld ReAct code agent; the model writes one python cell per step, executed against the app APIs; a task ends when the
cell calls apis.supervisor.complete_task()). A patch is a Python module that may define any subset of:
  HISTORY_LENGTH: int in [0, 20]            # how many previous (assistant cell, execution output) turns stay in the chat (default 20)
  TEMPERATURE: float in [0.0, 1.0]          # sampling temperature (default 0.4)
  def format_prompt(prompt: str, state: dict) -> str
      # prompt = the latest user turn: at step 0 the task ("My name is ...\nTask: <instruction>"), afterwards "Output:\n```\n<execution output of the
      # previous cell>\n```" (an error output starts with "Execution failed. Traceback:"). Return the text to send. state = per-task dict you own.
  def parse_action(response: str, admissible: list, state: dict) -> str
      # Return the python code to execute (default: the first ```python fenced block). admissible is always [] here.
  def retry_policy(attempt: int, response: str, action: str, admissible: list, state: dict) -> dict | None
      # Called only when NO code could be parsed (attempt 1, 2). Return None or {"extra_instruction": str, "temperature": float}.
  def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None
      # Called after each executed cell: observation = previous output, action = the code, next_observation = its output.
  def choose_fallback(admissible: list, state: dict) -> str
      # Called when still no code: return code to execute (default: print(apis.api_docs.show_app_descriptions())).
Allowed imports: re, json, math, random, collections, itertools, string. No file/network access. Only these names at top level."""
# ---------------- evaluation via SLURM ----------------
def submit(tag, patch, seed, ngames=NG, manifest=MAN, extra=""):
    if ARENA == "appworld" and BACKEND == "local":
        while int(subprocess.run(["bash", "-c", "squeue -h -u ymeng3 -o %j | grep -c -E '^(lean|aw-m1)$'"], capture_output=True).stdout.decode().strip() or 0) >= int(os.environ.get('LL_MAXJOBS', '2')): time.sleep(30)
    jf = f"{PD}/job_{tag}_s{seed}.txt"; open(jf, "w").write(f"{tag} {patch} {seed} {ngames}\n")
    if BACKEND == "local":
        env = f"ALL,JOBS_FILE={jf},BOS_MANIFEST={manifest},BOS_HOST_FILE={os.environ.get('BOS_HOST_FILE', '/net/scratch/ymeng3/local_llm/host')},BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24{extra}"; sb = "run_eval_local.sbatch"
    else:
        env = f"ALL,JOBS_FILE={jf},BOS_MANIFEST={manifest},BOS_MODEL={os.environ.get('BOS_MODEL','qwen/qwen3.8-27b')},BOS_PROVIDER=DeepInfra,BOS_FALLBACKS=0,BOS_REASONING_OFF=1,BOS_PRICE_IN=0.150e-6,BOS_PRICE_OUT=1.875e-6,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_GUARD_USD=202,BOS_WORKERS=16{extra}"; sb = "run_eval.sbatch"
    if ARENA == "appworld":
        tasks = os.environ.get("LL_TASKS", ""); tk = f",BOS_TASKS={tasks}" if tasks else ""; steps = f",BOS_AW_STEPS={os.environ['BOS_AW_STEPS']}" if os.environ.get("BOS_AW_STEPS") else ""
        if BACKEND == "local":
            env = f"ALL,JOBS_FILE={jf},BOS_MODEL={os.environ.get('BOS_MODEL','qwen/qwen3.8-27b')},BOS_THINK_OFF=1,BOS_TIMEOUT=300,BOS_HOST_FILE={os.environ.get('BOS_HOST_FILE','/net/scratch/ymeng3/local_llm/host')},BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_GUARD_USD=202,BOS_TIMEOUT=900,BOS_WORKERS={os.environ.get('LL_WORKERS','16')}{tk}{steps}{extra}"; sb = "run_aw_local.sbatch"
        else:
            env = f"ALL,JOBS_FILE={jf},BOS_MODEL={os.environ.get('BOS_MODEL','qwen/qwen3.8-27b')},BOS_PRICE_IN=0.150e-6,BOS_PRICE_OUT=1.875e-6,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_GUARD_USD=202,BOS_WORKERS=6{tk}{steps}{extra}"; sb = "run_aw_api.sbatch"
    j = subprocess.check_output(["sbatch", "--parsable", "--job-name=lean", "--array=0-0", "--time=02:30:00", f"--export={env}", sb], cwd=(AW if ARENA == "appworld" else R)).decode().strip().split(";")[0]
    log(f"  submit {tag} s{seed} n{ngames} -> {j}"); return j
def wait(jobs):
    while any(subprocess.run(["squeue", "-h", "-j", j], capture_output=True).stdout.strip() for j in jobs): time.sleep(45)
    time.sleep(8)
def wins(tag, seed):
    f = f"{RES}/results/{tag}_seed{seed}.json"
    if not os.path.exists(f): return None
    d = json.load(open(f)); return dict(zip(d.get("games_actual") or d["games"], [int(w) for w in d["won"]]))
def ensure(tag, patch, seed, ngames=NG, manifest=MAN, extra="", tries=3):
    for _ in range(tries):
        w = wins(tag, seed)
        if w is not None: return w
        wait([submit(tag, patch, seed, ngames, manifest, extra)])
    raise RuntimeError(f"no result for {tag} s{seed}")
def paired(a, b): gs = [g for g in a if g in b]; return sum(a[g] for g in gs), sum(b[g] for g in gs), len(gs)
# ---------------- units / patches ----------------
def top(src):
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name in HOOKS: out[n.name] = ast.unparse(n)
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id in HOOKS for x in n.targets): out[n.targets[0].id] = ast.unparse(n)
    return out
def units(cand_src, parent_src): c, p = top(cand_src), top(parent_src); return [u for u in c if c[u] != p.get(u)] + [u for u in p if u not in c]
def revert(cand_src, parent_src, us):
    """replace each unit in `us` by the parent's version (or drop it if the parent lacks it)."""
    p = top(parent_src); t = ast.parse(cand_src); body = []
    for n in t.body:
        nm = n.name if isinstance(n, ast.FunctionDef) else (n.targets[0].id if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) else None)
        if nm in us:
            if nm in p: body.append(ast.parse(p[nm]).body[0])
            continue
        body.append(n)
    present = {n.name if isinstance(n, ast.FunctionDef) else (n.targets[0].id if isinstance(n, ast.Assign) else None) for n in body}
    for u in us:
        if u in p and u not in present: body.append(ast.parse(p[u]).body[0])
    t.body = body; return ast.unparse(t) + "\n"
# ---------------- proposer ----------------
def propose(S, t):
    parent_src = open(S["parent"]).read(); mem = "\n".join(f"- round {h['round']}: {h['name']} -> {h['verdict']} ({h.get('detail','')})" for h in S["history"][-8:]) or "(none yet)"
    fails = failure_profile(S)
    ctx = (f"CURRENT PARENT HARNESS PATCH (your candidate must be a COMPLETE module; keep what works, change 2-4 hooks/constants with ONE composition hypothesis):\n```python\n{parent_src}\n```\n\n"
           f"PARENT FAILURE PROFILE on the training games:\n{fails}\n\nEARLIER ROUNDS (do not repeat):\n{mem}\n\n"
           "Output exactly:\nNAME: <snake_case>\nCOMPOSITION_HYPOTHESIS: <one sentence: which failure this fixes and why these units together>\n```python\n<module>\n```")
    cands = []; att = 0
    while len(cands) < K and att < 2 * K:
        att += 1
        try: resp = A.gpt4o([{"role": "system", "content": A.PROPOSER_SYS.replace("embodied household tasks (ALFWorld)", "multi-app tool-use tasks (AppWorld: the model writes python cells that call app APIs)") if ARENA == "appworld" else A.PROPOSER_SYS}, {"role": "user", "content": (AW_API_DOC if ARENA == "appworld" else A.HARNESS_API_DOC) + "\n\n" + ctx + f"\n\nAlready proposed this round: {[c['name'] for c in cands]}. Propose ONE new candidate."}], temperature=1.0, max_tokens=1800)
        except Exception as e: log("proposer error", str(e)[:80]); time.sleep(5); continue
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp); hy = re.search(r"COMPOSITION_HYPOTHESIS:\s*([^\n]+)", resp)
        src = m.group(1).strip() + "\n" if m else None
        if not src or not A.validate_patch(src)[0]: continue
        us = units(src, parent_src)
        if not us: continue
        name = f"LL_r{t}_c{len(cands)+1}_{(nm.group(1) if nm else 'cand')[:28]}"; p = f"{PD}/{name}.py"; open(p, "w").write(src)
        cands.append({"name": name, "path": p, "units": us, "hyp": (hy.group(1)[:300] if hy else "")}); log(f"  cand {name} units={us}")
    return cands
def failure_profile(S):
    f = f"{RES}/results/{S.get('parent_tag','')}_seed1.json"
    if not os.path.exists(f): return "(no logged parent pass yet)"
    if ARENA == "appworld":
        d = json.load(open(f)); lost = [(t, G, tr) for t, w, G, tr in zip(d["games"], d["won"], d["G"], d["traj"]) if not w]
        errs = sum(sum(x["exec_error"] for x in tr) for _, _, tr in lost); part = sum(1 for _, G, _ in lost if G and 0 < G < 1)
        ex = []
        for t, G, tr in lost[:4]:
            bad = [x for x in tr if x["exec_error"]][:1] or tr[-2:-1]
            ex.append(f"  task {t} (goal checks passed {G:.2f}): last cells -> " + " || ".join(f"CODE: {x['code'][:160]!r} OUT: {x['out'][:120]!r}" for x in (bad + tr[-1:])[:2]))
        return f"{sum(d['won'])}/{len(d['won'])} tasks completed. Lost {len(lost)}: {part} passed some goal checks (did part of the task then went wrong), {len(lost)-part} passed none. Execution errors in lost tasks: {errs}. Examples:\n" + "\n".join(ex)
    d = json.load(open(f)); st = collections.Counter(); dead = 0; n = 0
    for w, tr in zip(d["won"], d["traj"]):
        if w: continue
        n += 1; acts = [s["action"] for s in tr]; obs = [s.get("obs", "") for s in tr]
        picked = any(a.startswith("take") and "You pick up" in o for a, o in zip(acts, obs)); placed = any(re.match(r"(move|put) ", a) and ("You move" in o or "You put" in o) for a, o in zip(acts, obs))
        st["never found/picked the object" if not picked else "picked but never placed" if not placed else "placed but task not satisfied"] += 1; dead += sum(1 for s in tr if not s["admissible"])
    return f"{sum(d['won'])}/{len(d['won'])} won. Losses by stage: {dict(st)}. Inadmissible (wasted) steps in losses: {dead} (mean {dead/max(n,1):.1f} per lost game)."
# ---------------- one round ----------------
def run_round(S):
    t = S["round"]; parent = S["parent"]; ptag = S.get("parent_tag") or f"LL_parent_r{t}"; S["parent_tag"] = ptag
    log(f"=== ROUND {t} parent={os.path.basename(parent)}")
    pw1 = ensure(ptag, parent, 1); cands = propose(S, t); S_save(S)
    jobs = [(c, submit(c["name"], c["path"], 1)) for c in cands]; wait([j for _, j in jobs])
    scored = []
    for c, _ in jobs:
        w = wins(c["name"], 1)
        if w is None: log(f"  {c['name']} no result"); continue
        cw, pw, n = paired(w, pw1); c["wins"] = cw; c["parent_wins"] = pw; c["d"] = cw - pw; scored.append(c); log(f"  {c['name']}: {cw} vs parent {pw} (d {c['d']:+d})")
    improved = sorted([c for c in scored if c["d"] >= 2], key=lambda c: -c["d"])
    for c in scored:
        if c["d"] < 2: S["history"].append({"round": t, "name": c["name"], "verdict": "eliminated", "detail": f"{c['wins']} vs parent {c['parent_wins']}"})
    if not improved: log("  no candidate beat the parent by >=2 -> parent kept"); S["round"] += 1; S_save(S); return
    best = improved[0]; csrc = open(best["path"]).read(); psrc = open(parent).read(); cw1 = wins(best["name"], 1)
    # ---- component credit for the changed units (up to 3), paired against the candidate's own pass
    credit = {}; pend = {}
    for u in best["units"][:3]:
        off_src = revert(csrc, psrc, [u]); op = f"{PD}/{best['name']}_off_{u[:6]}.py"; open(op, "w").write(off_src)
        if not A.validate_patch(off_src)[0]: log(f"  unit {u}: OFF patch invalid, skipped"); continue
        if u in LOCAL and ARENA == "alfworld":
            kind = "fallback" if u == "choose_fallback" else "retry" if u == "retry_policy" else "parse"; s = f"ll_{best['name']}_{u[:6]}"
            subprocess.call(["python3", f"{H}/build_probeL.py", best["name"], kind, best["path"], op, s, "48", "1"], cwd=R, stdout=open(f"{R}/lean_loop.log", "a"), stderr=subprocess.STDOUT)
            if os.path.exists(f"{R}/probeL/{s}_manifest.txt") and os.path.getsize(f"{R}/probeL/{s}_manifest.txt") > 0:
                pend[u] = ("local", s, submit(f"PL_{s}_OFF_rep1", op, 1, 48, f"{R}/probeL/{s}_manifest.txt", f",BOS_REPLAY={R}/probeL/{s}_replay.json")); continue
        pend[u] = ("global", op, submit(f"{best['name']}_off_{u[:6]}_n16", op, 1, 16))
    wait([v[2] for v in pend.values()])
    for u, (kind, x, _) in pend.items():
        if kind == "local":
            w = wins(f"PL_{x}_OFF_rep1", 1) or {}; cw, ow, n = paired(cw1, w); credit[u] = {"on": cw, "off": ow, "n": n, "kind": "local"}
        else:
            n = 16; w = wins(f"{best['name']}_off_{u[:6]}_n{n}", 1) or {}
            while True:
                cw, ow, nn = paired(cw1, w); h = nn // 2; gs = [g for g in w if g in cw1]; d1 = sum(cw1[g] - w[g] for g in gs[:h]); d2 = sum(cw1[g] - w[g] for g in gs[h:])
                if (abs(cw - ow) >= 3 and (d1 > 0) == (d2 > 0) and d1 * d2 != 0) or n >= 48: break
                n += 16; wait([submit(f"{best['name']}_off_{u[:6]}_n{n}", x, 1, n)]); w = wins(f"{best['name']}_off_{u[:6]}_n{n}", 1) or w
            credit[u] = {"on": cw, "off": ow, "n": nn, "kind": "global"}
        c_ = credit[u]; c_["d"] = c_["on"] - c_["off"]; c_["verdict"] = "harmful" if c_["d"] <= -2 else "helpful" if c_["d"] >= 2 else "near-zero"; log(f"  unit {u}: ON {c_['on']} OFF {c_['off']} n {c_['n']} -> {c_['verdict']}")
    best["credit"] = credit; harmful = [u for u, c_ in credit.items() if c_["verdict"] == "harmful"]
    # ---- lean candidate
    final = best; final_tag = best["name"]
    if harmful:
        lsrc = revert(csrc, psrc, harmful); lp = f"{PD}/{best['name']}_lean.py"; open(lp, "w").write(lsrc); ltag = f"{best['name']}_lean"
        if A.validate_patch(lsrc)[0] and units(lsrc, psrc):
            lw = ensure(ltag, lp, 1); lc, lpw, _ = paired(lw, pw1); log(f"  lean (-{harmful}): {lc} vs parent {lpw} | full candidate {best['wins']}")
            if lc >= best["wins"]: final = {"name": ltag, "path": lp, "wins": lc, "units": [u for u in best["units"] if u not in harmful]}; final_tag = ltag
    # ---- confirm on seed 2 and commit
    pw2 = ensure(f"{ptag}", parent, 2); fw2 = ensure(final_tag, final["path"], 2); f2, p2, _ = paired(fw2, pw2)
    total_gain = (final["wins"] - best["parent_wins"]) + (f2 - p2); commit = f2 >= p2 and total_gain >= 3
    log(f"  seed2: {final_tag} {f2} vs parent {p2} | total gain over 2 seeds {total_gain:+d} -> {'COMMIT' if commit else 'keep parent'}")
    S["history"].append({"round": t, "name": final_tag, "verdict": "committed" if commit else "not confirmed", "detail": f"s1 {final['wins']} vs {best['parent_wins']}, s2 {f2} vs {p2}; credit {json.dumps({u: c_['verdict'] for u, c_ in credit.items()})}; harmful reverted {harmful}"})
    with open(LED, "a") as f: f.write(f"\n{time.strftime('%Y-%m-%d %H:%M')} LEAN LOOP round {t} ({BACKEND}): parent {os.path.basename(parent)} s1 {best['parent_wins']} | best cand {best['name']} s1 {best['wins']} units {best['units']} | credit {json.dumps(credit)} | final {final_tag} s1 {final['wins']} s2 {f2} vs parent s2 {p2} -> {'COMMIT' if commit else 'keep parent'}\n")
    if commit: S["parent"] = final["path"]; S["parent_tag"] = final_tag
    S["round"] += 1; S_save(S)
if __name__ == "__main__":
    S = S_load(); rounds = int(os.environ.get("LL_ROUNDS", "4"))
    for _ in range(rounds):
        try: run_round(S)
        except Exception as e: log("ROUND ERROR", repr(e)[:200]); S_save(S); raise
    log("LEAN LOOP done; parent =", S["parent"])
