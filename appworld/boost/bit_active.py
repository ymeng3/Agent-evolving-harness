"""Active sampling for BIT (MATH_FORMALIZATION_v2 §3, §6; BOOSTED_INTERVENTION_TREES_v0 §6; prereg A27).

Two allocation problems, both driven by the posterior instead of uniform seeds:
 tasks  : which discovery tasks to re-run (extra seeds, task subset only) so that the memory tree gets same-task won/lost contrasts
          (what the hindsight self-proposer needs to see a pattern) and more firing states for candidates.
          score_t = |g_t| * h_t / (n_t + 1) + kappa * sd_t   with Beta(1+wins, 1+losses) per task under the CURRENT base harness:
          boundary tasks (p ~ 0.5) with few runs first; always-solved tasks get ~0; never-solved tasks get the exploration term only
          (they may be environment / ground-truth issues). Thompson sampling over the same posterior is used to break ties.
 cands  : which candidates get extra branch repetitions (top-two Thompson on the pooled rank-1 posterior of bit_lowrank.py):
          candidates with P(beta>0) in [lo, hi] (undecided) and >= 2 states, ranked by posterior sd of a-bar.
usage:
  python boost/bit_active.py tasks --runs A,B --instr I --n-tasks 12 --seeds 3,4,5 --env-file E --tag CC_BIT_R2act_disc --out bit/R2/active_tasks
  python boost/bit_active.py cands --lowrank-json bit/R1/lowrank.json [--lo 0.3 --hi 0.95]"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bit_common import load_episodes


def task_scores(eps, kappa=0.5, seed=0):
    by = {}
    for e in eps: by.setdefault(e["task"], []).append(bool(e["won"]))
    rng = np.random.default_rng(seed); out = []
    for t, ws in by.items():
        a, b = sum(ws), len(ws) - sum(ws); al, be = 1 + a, 1 + b; p = al / (al + be); g, h = p - 1, p * (1 - p)
        sd = (al * be / ((al + be) ** 2 * (al + be + 1))) ** 0.5
        out.append({"task": t, "n": len(ws), "wins": a, "p": p, "score": abs(g) * h / (len(ws) + 1) + kappa * sd,
                    "thompson": float(rng.beta(al, be))})
    return sorted(out, key=lambda r: (-r["score"], abs(r["thompson"] - 0.5)))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tasks"); t.add_argument("--runs", required=True); t.add_argument("--instr", required=True)
    t.add_argument("--n-tasks", type=int, default=12); t.add_argument("--seeds", default="3,4,5"); t.add_argument("--env-file", default="")
    t.add_argument("--tag", default="CC_BIT_act_disc"); t.add_argument("--out", default=""); t.add_argument("--exclude", default="")
    c = sub.add_parser("cands"); c.add_argument("--lowrank-json", required=True); c.add_argument("--lo", type=float, default=0.3)
    c.add_argument("--hi", type=float, default=0.95); c.add_argument("--k", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "tasks":
        eps = [e for e in load_episodes(a.runs.split(","), json.load(open(a.instr, encoding="utf-8"))) if not e["crashed"]]
        ex = set(x for x in a.exclude.split(",") if x)
        sc = [r for r in task_scores(eps) if r["task"] not in ex]; pick = sc[:a.n_tasks]
        for r in pick: print(f"  {r['task']:12s} n={r['n']} wins={r['wins']} p={r['p']:.2f} score={r['score']:.3f}")
        if a.out:
            os.makedirs(a.out, exist_ok=True); json.dump([r["task"] for r in pick], open(os.path.join(a.out, "tasks.json"), "w"))
            json.dump(sc, open(os.path.join(a.out, "scores.json"), "w"), indent=1)
            if a.env_file:
                env = [x for x in open(a.env_file).read().split() if "=" in x and not x.startswith(("BOS_TASKS=", "BOS_REPLAY=", "BOS_HINTS="))]
                patch = next((open(a.env_file).read().split()[i + 1] for i, x in enumerate(open(a.env_file).read().split()) if x == "--patch"), "none")
                srv = os.path.join("/root/autodl-tmp/cc/Agent-evolving-harness/appworld", a.out).replace("\\", "/")
                lines = [" ".join(env + [f"BOS_TASKS={srv}/tasks.json", "python", "bos_appworld_v3.py", "eval", "--patch", patch, "--seed", s,
                                          "--tag", a.tag, "--workers", "8"]) for s in a.seeds.split(",")]
                open(os.path.join(a.out, "jobs.txt"), "w", newline="\n").write("".join(l + "\n" for l in lines)); print(f"{len(lines)} jobs -> {a.out}/jobs.txt")
    else:
        rows = json.load(open(a.lowrank_json, encoding="utf-8"))
        und = [r for r in rows if a.lo <= r["p_pos"] <= a.hi and r["states"] >= 2]
        und.sort(key=lambda r: -(r["a_hi90"] - r["a_lo90"]))
        for r in und[:a.k]: print(f"  allocate more reps: {r['cid']}  P(beta>0)={r['p_pos']:.2f}  a={r['a_bar']:+.3f} [{r['a_lo90']:+.3f},{r['a_hi90']:+.3f}]  states={r['states']}")
        if not und: print("  no undecided candidates")


if __name__ == "__main__":
    main()
