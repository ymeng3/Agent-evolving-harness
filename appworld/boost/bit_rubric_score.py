"""Rubric score R(tau) = sum_k w_k * phi_k(tau) of a set of intervention trees (MATH_FORMALIZATION_v2 §5a: predictive head).
w_k = the within-task Newton weight from screening (screen.json "w_pred"; refs get their own w_pred too). phi_k = the tree fires anywhere in
the episode (offline simulation). Reports, on any runs (e.g. held-out validation logs of the base harness): pooled AUC of -R for failure,
within-task pair accuracy (same-task won vs lost pairs), and per-tree fire rates. A higher R = more evidence of failure.
usage: python boost/bit_rubric_score.py --screen screen.json [--only-kept] --runs A,B --instr I"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bit_common import load_episodes, make_pairs


def auc(score, y):
    """P(score of a lost episode > score of a won episode), ties 1/2."""
    s = np.asarray(score, float); y = np.asarray(y, bool); pos, neg = s[~y], s[y]
    if not len(pos) or not len(neg): return float("nan")
    return float(((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--screen", required=True); ap.add_argument("--only-kept", action="store_true")
    ap.add_argument("--runs", required=True); ap.add_argument("--instr", required=True); ap.add_argument("--timeout", type=float, default=120)
    a = ap.parse_args()
    import bit_rubric as BR
    sc = json.load(open(a.screen, encoding="utf-8"))
    trees = [c for c in sc["candidates"] if c.get("error") is None and c.get("spec") and c.get("w_pred") is not None
             and (c.get("kept") or c.get("ref") or not a.only_kept) and abs(c["w_pred"]) > 1e-9]
    instr = json.load(open(a.instr, encoding="utf-8"))
    eps = [e for e in load_episodes(a.runs.split(","), instr) if not e["crashed"] and not e["has_replay"]]
    y = [e["won"] for e in eps]; R = np.zeros(len(eps)); idx = {e["eid"]: i for i, e in enumerate(eps)}
    print(f"{len(eps)} episodes ({sum(y)} won), {len(trees)} trees")
    for c in trees:
        res = BR.simulate(BR.compile_patch([c["spec"]]), eps, timeout_s=a.timeout)
        phi = np.array([1.0 if res[e["eid"]]["fires"] else 0.0 for e in eps]); R += c["w_pred"] * phi
        print(f"  {c['cid']:34s} w={c['w_pred']:+.3f} fires {int(phi.sum()):3d}  P|L {phi[~np.array(y)].mean() if not all(y) else float('nan'):.2f}  P|W {phi[np.array(y)].mean():.2f}")
    I, J, _ = make_pairs(eps)
    pacc = float(np.mean([0.5 if R[i] == R[j] else float(R[j] > R[i]) for i, j in zip(I, J)])) if len(I) else float("nan")
    print(f"rubric score R: pooled AUC(failure) = {auc(R, y):.3f}; within-task pair accuracy = {pacc:.3f} over {len(I)} same-task pairs")


if __name__ == "__main__":
    main()
