"""Validation read-out for v2 states (admission never used validation). Programmatic dimensions are recomputed on validation with the
DISCOVERY vocabulary; semantic dimensions are judge-scored on validation (same blind judge, cached). Then for each round: fit on discovery
with the dimensions admitted up to that round, score validation. Also: compare arms (paired task-cluster bootstrap of per-trajectory log-loss).
usage: python boost/rescore_v2.py score OUT/ARM/state.json --val V1.json,V2.json --instr instructions.json
       python boost/rescore_v2.py compare OUT ARM_A ARM_B [ARM_C ...]"""
import json, os, shutil, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, features as FT, judge as JG


def score(state_path, val, instr_path, workers=12):
    s = json.load(open(state_path)); assert s["L"] == C.L
    rd = [r for r in C.load_runs(s["disc"].split(",")) if r["at_risk"]]; rv = [r for r in C.load_runs(val.split(",")) if r["at_risk"]]
    yd = np.array([r["y"] for r in rd], float); yv = np.array([r["y"] for r in rv], float); instr = json.load(open(instr_path))
    missing = [r["task"] for r in rv if r["task"] not in instr]
    if missing: sys.exit(f"instructions missing for {len(set(missing))} validation tasks")
    names, _, VM = FT.pool(rv, C.L, tuple(s["vocab"])); J = None; vcols = []
    for d in s["admitted"]:
        if d["kind"] == "prog": vcols.append(VM[:, names.index(d["name"])])
        else:
            J = J or JG.Judge(os.path.join(os.path.dirname(os.path.dirname(state_path)), "judge_cache"), workers)
            maj, _ = J.score(d["desc"], [(f"{r['tag']}|{r['seed']}|{r['task']}", instr[r["task"]][:400], C.window(r["cells"])) for r in rv])
            vcols.append(np.array([np.nan if m is None else float(m) for m in maj]))
    for rec in s["rounds"]:
        idx = [j for j, d in enumerate(s["admitted"]) if d["admitted_round"] <= rec["round"]]
        Fd = np.array([s["admitted"][j]["values"] for j in idx], float).T if idx else np.zeros((len(rd), 0))
        Fv = np.array([vcols[j] for j in idx], float).T if idx else np.zeros((len(rv), 0))
        m, pv = C.fit_eval(Fd, yd, Fv, yv); rec["val"] = {x: m[x] for x in ("logloss", "auc", "brier")}; rec["val_p"] = pv.tolist()
        print(f"{s['arm']} round {rec['round']}: k={len(idx)} val_ll={m['logloss']:.4f} val_auc={m['auc']:.3f}")
    s.update(val=val, val_tasks=[r["task"] for r in rv], val_y=yv.tolist(), val_judge_stats=J.stats if J else None)
    shutil.copy(state_path, state_path + ".bak"); json.dump(s, open(state_path, "w"), indent=1)


def compare(out, arms):
    S = {a: json.load(open(os.path.join(out, a, "state.json"))) for a in arms}
    y = np.array(S[arms[0]]["val_y"]); g = S[arms[0]]["val_tasks"]
    L = {a: C.per_traj_logloss(y, np.array(S[a]["rounds"][-1]["val_p"])) for a in arms}
    for a in arms:
        assert S[a]["val_tasks"] == g, "validation sets differ"
        print(f"{a:11s} admitted {[d['kind'] + ':' + d['name'] for d in S[a]['admitted']]}  final val_ll {L[a].mean():.4f}  auc {S[a]['rounds'][-1]['val']['auc']:.3f}")
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            d, lo, hi = C.cluster_bootstrap_diff(g, L[a], L[b]); print(f"{a} - {b}: {d:+.4f}  90% CI [{lo:+.4f}, {hi:+.4f}]  {'(a better)' if hi < 0 else '(b better)' if lo > 0 else ''}")


if __name__ == "__main__":
    if sys.argv[1] == "score":
        import argparse; ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("state"); ap.add_argument("--val", required=True); ap.add_argument("--instr", required=True)
        ap.add_argument("--workers", type=int, default=12); a = ap.parse_args(); score(a.state, a.val, a.instr, a.workers)
    else: compare(sys.argv[2], sys.argv[3:])
