"""Branch-at-fire readout (prereg A13). For each branch state (task, origin seed, slot) compare the continuation outcome under each
nudge variant with the plain continuation ('none'), paired by state. Unit for inference = task (states of the same task across origin seeds
and reps are averaged first); sign-flip test + task bootstrap. Also splits by the logged run's outcome (won / lost): a nudge that helps
lost states but hurts won states is the c(sigma) < 0 region of MATH_FORMALIZATION section 5.
usage: python boost/branch_readout.py --build branch/NAME --results results [--tag CC_BR]"""
import argparse, collections, glob, json, os
import numpy as np


def signflip(x, B=20000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); obs = abs(x.mean())
    return float(((np.abs((rng.choice([-1, 1], (B, len(x))) * x).mean(1)) >= obs - 1e-12).mean()))


def boot(x, B=5000, seed=0):
    x = np.asarray(x, float); rng = np.random.default_rng(seed); m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return float(np.quantile(m, 0.05)), float(np.quantile(m, 0.95))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--build", required=True); ap.add_argument("--results", default="results")
    ap.add_argument("--tag", default="CC_BR"); ap.add_argument("--logged", default="", help="comma list of the H1 runs the branches came from (for won/lost split)")
    a = ap.parse_args()
    logged = {}
    for p in [x for x in a.logged.split(",") if x]:
        d = json.load(open(p, encoding="utf-8"))
        for t, w in zip(d["games"], d["won"]): logged[(t, d["seed"])] = bool(w)
    for m in json.load(open(os.path.join(a.build, "manifest.json"))):
        slot, seed = m["slot"], m["seed"]; meta = json.load(open(os.path.join(m["dir"], "meta.json")))
        out = collections.defaultdict(dict)   # variant -> tid -> [won,...] (reps)
        for f in glob.glob(os.path.join(a.results, f"{a.tag}_{slot}_*_o{seed}*_seed{seed}.json")):
            d = json.load(open(f, encoding="utf-8")); v = os.path.basename(f)[len(a.tag) + len(slot) + 2:].split("_o")[0]
            for t, w, cr in zip(d["games"], d["won"], d.get("crashed") or [None] * len(d["games"])):
                if not cr: out[v].setdefault(t, []).append(float(w))
        if "none" not in out: print(f"{slot} s{seed}: no 'none' run yet ({sorted(out)})"); continue
        print(f"\n== slot {slot}, origin seed {seed}: {m['n']} states {m['dets']}; variants {sorted(out)}")
        for v in sorted(out):
            ts = sorted(set(out[v]) & set(out["none"]))
            print(f"  {v:9s} n={len(ts):3d} win={np.mean([np.mean(out[v][t]) for t in ts]):.3f}", end="")
            if v == "none": print(); continue
            diff = np.array([np.mean(out[v][t]) - np.mean(out["none"][t]) for t in ts]); lo, hi = boot(diff)
            print(f"  vs none {diff.mean():+.3f} [90% CI {lo:+.3f},{hi:+.3f}] p={signflip(diff):.3f}", end="")
            for lab, sel in (("logged-won", True), ("logged-lost", False)):
                dd = [x for x, t in zip(diff, ts) if logged.get((t, seed)) is sel]
                if dd: print(f" | {lab} n={len(dd)} {np.mean(dd):+.3f}", end="")
            by = collections.defaultdict(list)
            for x, t in zip(diff, ts): by[meta[t]["det"]].append(x)
            print(" | by det " + " ".join(f"{k}:{np.mean(x):+.2f}(n={len(x)})" for k, x in sorted(by.items())))


if __name__ == "__main__":
    main()
