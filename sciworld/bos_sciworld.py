"""SciWorld harness with the same 5-hook patch API as bos_alfworld (format_prompt, parse_action, retry_policy, memory_update,
choose_fallback; constants HISTORY_LENGTH, TEMPERATURE). Per-step log: action, valid, score, score delta, obs, component flags.
Usage: eval --patch P|none --seed S --tag T [--n-games N] [--workers W]     env: BOS_SW_MANIFEST (task_name<TAB>variation lines)"""
import os, sys, json, re, time, threading, argparse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld")
import bos_alfworld as A          # Backbone, validate_patch, load_patch, GUARD, default_parse, MODEL
OUT = "/net/scratch/ymeng3/bos_sciworld"; MANIFEST = os.environ.get("BOS_SW_MANIFEST", f"{OUT}/manifests/sw48.txt")
STEP_LIMIT = int(os.environ.get("BOS_SW_STEPS", "40")); SIMPL = os.environ.get("BOS_SW_SIMPL", "easy")
TEMPLATE = ("You are an expert agent operating in the ScienceWorld environment, which is a text-based virtual environment centered around accomplishing tasks from the elementary science curriculum.\n"
    "Your current task is: {task}\n"
    "Prior to this step, you have already taken {n} step(s). Below are the most recent {h} observations and the corresponding actions you took: {hist}\n"
    "You are now at step {cur} and your current observation is: {obs}\n"
    "Your admissible actions of the current situation are:\n{adm}\n\n"
    "Note: 'focus on X' is graded — only focus on the exact object the task names, after you have found it.\n"
    "Now it's your turn to take an action.\nYou should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.\n"
    "Once you've finished your reasoning, you should choose an admissible action for the current step and present it within <action> </action> tags.")
STOP = {"task","your","first","then","substance","object","also","acceptable","without","boiling","point","combusting","focus","find","living","thing","room","location","them","that","this","with","from","into","which","have","when","after","before","take","actions","will","cause","change","state","matter","either","using","named","known","unknown","most","should"}
def task_words(task): return set(re.findall(r"[a-z]{4,}", task.lower())) - STOP
def safe_adm(adm, task):
    tw = task_words(task); return [c for c in adm if not c.startswith("focus on") or any(w in c for w in tw)]
def build_prompt(task, hist, obs, adm, H):
    h = " ".join(f"[step {i+1}] observation: {o[:250]} | action: {a};" for i,(o,a) in enumerate(hist[-H:])) if hist else "(none)"
    return TEMPLATE.format(task=task, n=len(hist), h=min(H,len(hist)), hist=h, cur=len(hist)+1, obs=obs[:1500], adm=", ".join(adm[:160]))
def run_eval(patch_path, seed, tag, n_games=None, workers=8):
    from scienceworld import ScienceWorldEnv
    hooks = A.load_patch(patch_path) if patch_path not in (None, "none") else {}
    fp, pa, rp, mu, cf = (hooks.get(k) for k in ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback"))
    H = int(hooks.get("HISTORY_LENGTH", 5)); T = float(hooks.get("TEMPERATURE", 0.4))
    games = [l.rstrip("\n").split("\t") for l in open(MANIFEST) if l.strip()][: (n_games or 10**9)]
    bb = A.Backbone(T); lock = threading.Lock(); local = threading.local()
    def env():
        if not hasattr(local, "env"): local.env = ScienceWorldEnv("", envStepLimit=STEP_LIMIT * 3)
        return local.env
    def play(i):
        task, var = games[i][0], int(games[i][1]); e = env(); e.load(task, var, SIMPL); obs, info = e.reset(); desc = e.get_task_description()
        templates = e.get_possible_actions(); state = {}; hist = []; traj = []; score = 0.0; won = False; steps = 0
        for step in range(STEP_LIMIT):
            A.GUARD.check(); adm = safe_adm([c.lower() for c in e.get_valid_action_object_combinations()], desc); si0 = None
            prompt0 = build_prompt(desc, hist, obs, adm, H); prompt = prompt0; si = {"pc": 0, "calls": 1}
            try:
                if fp: prompt = fp(prompt, state)
            except Exception: pass
            si["pc"] = int(prompt != prompt0)
            resp, err = bb.call(prompt); action = None
            try: action = pa(resp, adm, state) if pa else A.default_parse(resp)
            except Exception: action = A.default_parse(resp)
            action = (action or "").strip().lower(); si["parse_chg"] = int(bool(pa) and action != A.default_parse(resp)); si["a0"] = action[:60]; si["a0_adm"] = int(action in adm)
            attempt = 0
            while rp and action not in adm and attempt < 2:
                attempt += 1
                try: pol = rp(attempt, resp, action, adm, state)
                except Exception: pol = None
                if not pol: break
                si["calls"] += 1
                resp, err = bb.call(prompt + ("\n\n" + pol.get("extra_instruction", "") if pol.get("extra_instruction") else ""), pol.get("temperature"))
                try: action = pa(resp, adm, state) if pa else A.default_parse(resp)
                except Exception: action = A.default_parse(resp)
                action = (action or "").strip().lower()
            si["retry_n"] = attempt; si["retry_chg"] = int(attempt > 0 and action != si["a0"]); si["fb"] = 0
            if action not in adm and cf:
                try:
                    fb = cf(adm, state); 
                    if fb in adm: action = fb; si["fb"] = 1
                except Exception: pass
            send = action if action else "look around"
            if send.startswith("focus on") and send not in adm: send = "look around"; si["focus_guard"] = 1   # harness safety: off-task focus never reaches the env
            nobs, reward, done, info = e.step(send)
            ns = float(info.get("score", 0.0)); traj.append({"step": step, "action": action[:120], "admissible": action in adm, "score": ns, "dscore": ns - score, "obs": nobs[:160], **si})
            try:
                if mu: mu(state, obs, action, nobs)
            except Exception: pass
            hist.append((obs, action)); obs = nobs; score = ns; steps += 1
            if done: won = bool(info.get("score", 0) >= 100) or bool(done and ns > 0 and ns >= 100); break
        return i, {"task": task, "variation": var, "won": bool(score >= 100), "score": score, "steps": steps, "traj": traj}
    results = [None] * len(games)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, r in ex.map(play, range(len(games))): results[i] = r
        if False: pass
    res = {"tag": tag, "patch": patch_path, "manifest": MANIFEST, "seed": seed, "model": A.MODEL, "history_length": H, "temperature": T, "n_games": len(games),
           "success_rate": sum(r["won"] for r in results) / len(games), "mean_score": sum(r["score"] for r in results) / len(games),
           "won": [r["won"] for r in results], "score": [r["score"] for r in results], "games": [f"{r['task']}\t{r['variation']}" for r in results],
           "steps": [r["steps"] for r in results], "traj": [r["traj"] for r in results], "calls": bb.calls, "api_errors": bb.errors, "error_types": bb.err_types,
           "tokens_in": bb.tok[0], "tokens_out": bb.tok[1], "finished": time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(f"{OUT}/results", exist_ok=True); json.dump(res, open(f"{OUT}/results/{tag}_seed{seed}.json", "w"))
    print(f"{tag} seed{seed}: success {res['success_rate']:.3f} mean_score {res['mean_score']:.1f} calls {bb.calls} api_errors {bb.errors}", flush=True)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--patch", default="none"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--tag", default="SW_F0"); ap.add_argument("--n-games", type=int, default=None); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(); run_eval(a.patch, a.seed, a.tag, a.n_games, a.workers)
