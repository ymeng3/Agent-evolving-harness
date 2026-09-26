"""AgentPRM-style go/no-go (2026-09-25): blind promise/progress judge on ON/OFF paired windows -> dV per component vs global gamma.
Usage: python prm_test.py [N_GAMES=16] [OUT]. Judge = local A3B via BOS_BASE_URL (harness Backbone). Not a trained PRM."""
import json, os, sys, random, re, statistics as st
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag"); sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld")
from p2_components import C; import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_alfworld"; NG = int(sys.argv[1]) if len(sys.argv) > 1 else 16; OUT = sys.argv[2] if len(sys.argv) > 2 else f"{R}/hag_prm_scores.json"
bb = A.Backbone(0.0); random.seed(7); W_BEFORE, W_AFTER = 3, int(os.environ.get("PRM_AFTER", "12")); ONLY = [x for x in os.environ.get("PRM_ONLY", "").split(";") if x]
def window(traj, t):
    lo = max(0, t - W_BEFORE); seg = traj[lo:t + W_AFTER]
    return "\n".join(f"{'>' if s['step'] == t else ' '} step {s['step']}: {s['action']}  ->  {s['obs'][:110]}" for s in seg)
def judge(task, wa, wb):
    p = (f"You are evaluating two alternative continuations of a household agent in a text game. The task: {task}\n"
         f"Both share the same history up to the step marked '>'; after that they diverge. Steps show action -> environment feedback.\n\n"
         f"=== Continuation A ===\n{wa}\n\n=== Continuation B ===\n{wb}\n\n"
         "For EACH continuation give two scores.\n"
         "promise (0-10): at the end of the shown steps, how likely is the agent to complete the task eventually?\n"
         "progress (-5..+5): compared with the state at '>', did these steps make the situation better (new locations/objects/clues found, "
         "closer to the goal) or worse (repetition, wasted steps, going backwards)?\n"
         'Reply with ONLY JSON: {"A":{"promise":x,"progress":y},"B":{"promise":x,"progress":y}}')
    r, err = bb.call(p); m = re.search(r"\{.*\}", r or "", re.S)
    try: j = json.loads(m.group(0)); return float(j["A"]["promise"]), float(j["A"]["progress"]), float(j["B"]["promise"]), float(j["B"]["progress"])
    except Exception: return None
rows = {}; prior = json.load(open(OUT)) if os.path.exists(OUT) else {}
for name, src, kind, cp, op, g in C:
    if ONLY and name not in ONLY: continue
    s = "p2_" + name.replace(" ", "_"); f = f"{R}/results/PL_{s}_OFF_rep1_seed1.json"; meta = f"{R}/probeL/{s}_meta.json"; cf = f"{R}/results/{src}_seed1.json"
    if not all(os.path.exists(x) for x in (f, meta, cf)): print(name, "pending"); continue
    if name in prior: rows[name] = prior[name]; continue
    off = json.load(open(f)); M = json.load(open(meta)); on = json.load(open(cf)); OFF_ = int(os.environ.get("PRM_OFFSET", "0")); order = [l.strip() for l in open(f"{R}/probeL/{s}_manifest.txt") if l.strip()][OFF_:OFF_ + NG]
    ga_off = off.get("games_actual") or off["games"]; ga_on = on.get("games_actual") or on["games"]; dP, dPP = [], []; nfail = 0
    for gme in order:
        if gme not in ga_off or gme not in ga_on: continue
        t = M[gme]["tstar"]; to = on["traj"][ga_on.index(gme)]; tf = off["traj"][ga_off.index(gme)]
        task = re.search(r"Your task is to: ([^\n]+)", to[0].get("obs", "") + " ") ; task = task.group(1) if task else gme.split("/")[-3]
        won, woff = window(to, t), window(tf, t); flip = random.random() < 0.5
        res = judge(task, woff if flip else won, won if flip else woff)
        if res is None: nfail += 1; continue
        pa, ga_, pb, gb = res; (pon, gon, poff, goff) = (pb, gb, pa, ga_) if flip else (pa, ga_, pb, gb)
        dP.append(pon - poff); dPP.append((pon + gon) - (poff + goff))
    rows[name] = {"gamma": g, "kind": kind, "n": len(dP), "judge_fail": nfail, "dV_promise": st.mean(dP) if dP else None, "dV_both": st.mean(dPP) if dPP else None}
    print(f"{name:18s} gamma {g:+6.1f}  dV_promise {rows[name]['dV_promise']:+.2f}  dV_both {rows[name]['dV_both']:+.2f}  n {len(dP)} fail {nfail}", flush=True)
    json.dump(rows, open(OUT, "w"), indent=1)
# read-out
def rank(v): return sorted(range(len(v)), key=lambda i: v[i])
def spearman(x, y):
    rx, ry = [0]*len(x), [0]*len(y)
    for r_, i in enumerate(rank(x)): rx[i] = r_
    for r_, i in enumerate(rank(y)): ry[i] = r_
    n = len(x); return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1)) if n > 2 else float("nan")
def cls(v, d): return "harmful" if v < -d else "helpful" if v > d else "neutral"
names = [k for k in rows if rows[k]["dV_promise"] is not None]; G = [rows[k]["gamma"] for k in names]
for key in ("dV_promise", "dV_both"):
    V = [rows[k][key] for k in names]; agree = sum(cls(g_, 3) == cls(v, 0.5) for g_, v in zip(G, V)) / len(V)
    commit_ok = sum((v > 0) == (g_ > 3) for g_, v in zip(G, V)) / len(V); base = sum(g_ > 3 for g_ in G) / len(G)
    print(f"{key}: n={len(V)} spearman(gamma)={spearman(G, V):+.2f} 3-class agree(delta 3 / 0.5)={agree:.2f} commit-agree(v>0 vs gamma>3)={commit_ok:.2f} [commit-all baseline={max(base,1-base):.2f}]")
print("judge calls", bb.calls, "errors", bb.errors)
