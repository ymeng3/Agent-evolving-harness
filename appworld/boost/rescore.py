"""Re-score a finished (or running) Stage-1 state on a validation set that did not exist when the loop started.
Admission never looks at validation data, so this is equivalent to the loop's own per-round read-out: for each round r the rubric is
the set of dimensions admitted at rounds <= r, fit on the discovery landmark set, scored on the validation landmark set.
usage: python boost/rescore.py OUT/ARM/state.json --val V1.json,V2.json   (rewrites val fields in place; keeps a backup)"""
import argparse, json, os, shutil, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("state"); ap.add_argument("--val", required=True); a = ap.parse_args()
    s = json.load(open(a.state)); assert s["L"] == C.L, f"L mismatch {s['L']} vs {C.L}"
    rd = [r for r in C.load_runs(s["disc"].split(",")) if r["at_risk"]]; rv = [r for r in C.load_runs(a.val.split(",")) if r["at_risk"]]
    yd = np.array([r["y"] for r in rd], float); yv = np.array([r["y"] for r in rv], float)
    vals = {}
    for d in s["rubric"]:
        fn = C.compile_detector(d["src"]); vals[d["name"] + "#" + str(d["round"])] = (C.run_detector(fn, rd)[0], C.run_detector(fn, rv)[0], d["round"])
    for rec in s["rounds"]:
        cols = [v for v in vals.values() if v[2] <= rec["round"]]
        Fd = np.array([c[0] for c in cols]).T if cols else np.zeros((len(rd), 0)); Fv = np.array([c[1] for c in cols]).T if cols else np.zeros((len(rv), 0))
        m, pv = C.fit_eval(Fd, yd, Fv, yv); rec["val"] = {x: m[x] for x in ("logloss", "auc", "brier")}; rec["val_p"] = pv.tolist()
        print(f"round {rec['round']}: k={len(cols)} val_ll={m['logloss']:.4f} val_auc={m['auc']:.3f}")
    s.update(val=a.val, val_tasks=[r["task"] for r in rv], val_y=yv.tolist(), val_source="rescore.py")
    shutil.copy(a.state, a.state + ".bak"); json.dump(s, open(a.state, "w"), indent=1)


if __name__ == "__main__":
    main()
