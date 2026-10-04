"""Paired, task-level readout on several outcome metrics (prereg A22 metric hierarchy).
  success : binary task success (primary)
  G       : fraction of the task's state tests passed (AppWorld 'no_op_fail' tests; denser, partial-credit outcome)
For each arm vs a base: per-task mean over runs, paired difference, sign-flip p and task-bootstrap 90% CI.
usage: python boost/multi_metric_readout.py --base H2=a.json,b.json --arm X=c.json,d.json [--arm ...]"""
import argparse, json
import numpy as np


def load(spec):
    name, files = spec.split("=", 1); per = {}
    for f in files.split(","):
        d = json.load(open(f, encoding="utf-8"))
        for t, w, g, cr in zip(d["games"], d["won"], d.get("G") or [None] * len(d["games"]), d.get("crashed") or [None] * len(d["games"])):
            if cr: continue
            per.setdefault(t, {"success": [], "G": []})
            per[t]["success"].append(float(w))
            per[t]["G"].append(float(g) if g is not None else float(w))
    return name, per, len(files.split(","))


def signflip(x, B=20000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); obs = abs(x.mean())
    return float((np.abs((rng.choice([-1, 1], (B, len(x))) * x).mean(1)) >= obs - 1e-12).mean())


def boot(x, B=5000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return float(np.quantile(m, 0.05)), float(np.quantile(m, 0.95))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); ap.add_argument("--arm", action="append", default=[]); a = ap.parse_args()
    bn, base, bk = load(a.base)
    print(f"{'arm':16s} runs | {'success':>7s} {'d':>7s} {'90% CI':>16s} {'p':>6s} | {'G':>6s} {'d':>7s} {'90% CI':>16s} {'p':>6s}")
    for spec in [a.base] + a.arm:
        n, per, k = load(spec); ts = sorted(set(per) & set(base)); row = f"{n:16s} {k:4d} |"
        for m in ("success", "G"):
            v = np.array([np.mean(per[t][m]) for t in ts]); b = np.array([np.mean(base[t][m]) for t in ts]); d = v - b
            if n == bn: row += f" {v.mean():7.3f} {'':>7s} {'':>16s} {'':>6s} |"
            else:
                lo, hi = boot(d); row += f" {v.mean():7.3f} {d.mean():+7.3f} [{lo:+.3f},{hi:+.3f}] {signflip(d):6.3f} |"
        print(row)


if __name__ == "__main__":
    main()
