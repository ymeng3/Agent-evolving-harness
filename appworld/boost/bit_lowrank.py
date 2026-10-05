"""Pooled (rank-1) estimate of a candidate's causal effect from branch-at-fire data (MATH_FORMALIZATION_v2 §7; prereg A26).

The per-state difference estimator wastes data: every state gets its own baseline and its own effect. Here
    y[s, arm, r] ~ Bernoulli(sigmoid(alpha_s + beta * 1{arm = cand}))       (effect beta shared across states = rank-1 in candidate x state)
    alpha_s ~ Normal(logit(V0_s), tau^2)                                     (state baseline, prior centred on V0_s)
    beta ~ Normal(0, sb^2)
V0_s = posterior mean of the memory-tree node at the firing step (Beta(1+wins, 1+losses) over the base logs). The logged episode itself is one
draw of the 'none' arm at that state (firing depends on the prefix only), so it is added as a free none sample (--use-logged).
The posterior of beta is computed EXACTLY on a grid: for each beta, every alpha_s is integrated out on its own 1-D grid. Several branch builds of
the same candidate (e.g. 2-rep and 4-rep builds) are pooled per (seed, task) state. Reports beta (log-odds), a-bar = mean_s
[sigmoid(alpha_s + beta) - sigmoid(alpha_s)] under the posterior, P(beta > 0), and the naive per-state difference for comparison.
usage: python boost/bit_lowrank.py --builds bit/R1/branch,bit/R1/branch_x4 --results results --runs <base runs> --instr I [--cid ...]"""
import argparse, collections, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bit_common import load_episodes, beta_stats

SIG = lambda x: 1.0 / (1.0 + np.exp(-x))


def collect(builds, results):
    """-> {cid: {(seed, task): {"cw","cn","nw","nn","eid","k","logged_won"}}} pooled over builds."""
    data = collections.defaultdict(dict)
    for b in builds:
        man = json.load(open(os.path.join(b, "manifest.json"), encoding="utf-8"))
        for c in man["cands"]:
            cid = c["cid"]
            for dd in c["dirs"]:
                meta = json.load(open(os.path.join(b, dd["dir"], "meta.json"), encoding="utf-8"))
                for j in man["jobs"]:
                    if j["cid"] != cid or j["dir"] != dd["dir"]: continue
                    p = os.path.join(results, f"{j['tag']}_seed{j['seed']}.json")
                    if not os.path.exists(p): continue
                    d = json.load(open(p, encoding="utf-8"))
                    for t, w, cr in zip(d["games"], d["won"], d.get("crashed") or [None] * len(d["games"])):
                        if cr or t not in meta: continue
                        st = data[cid].setdefault((dd["seed"], t), {"cw": 0, "cn": 0, "nw": 0, "nn": 0, **{k: meta[t][k] for k in ("eid", "k", "logged_won")}})
                        st["cw" if j["arm"] == "cand" else "nw"] += int(w); st["cn" if j["arm"] == "cand" else "nn"] += 1
    return data


def node_prior(eps, eid, k):
    """V0 = posterior mean of the trie node at the firing step (episodes sharing the logged prefix up to k)."""
    import bit_tree as BT
    e = next(x for x in eps if x["eid"] == eid); tries = node_prior.tries
    depth = next((i for i, s in enumerate(e["steps"]) if s["k"] == k), len(e["steps"]))
    v = BT.node_at(tries, e, depth); return beta_stats(len(v["won"]), len(v["lost"]))["p"]


def posterior(states, tau=1.5, sb=2.0, gb=np.linspace(-6, 6, 601), ga=np.linspace(-8, 8, 321)):
    """exact grid posterior of beta; returns dict with beta mean/CrI, P(beta>0), a-bar mean/CrI."""
    logpost = -0.5 * (gb / sb) ** 2; abar_given_b = np.zeros_like(gb)
    for st in states:
        m = np.log(st["v0"] / (1 - st["v0"]))
        la = -0.5 * ((ga - m) / tau) ** 2                                         # prior over alpha_s on its grid
        pn = SIG(ga)                                                              # none arm
        ll_none = st["nw"] * np.log(pn) + (st["nn"] - st["nw"]) * np.log(1 - pn)
        pc = SIG(ga[None, :] + gb[:, None])                                       # [beta, alpha]
        ll_cand = st["cw"] * np.log(pc) + (st["cn"] - st["cw"]) * np.log(1 - pc)
        lj = la[None, :] + ll_none[None, :] + ll_cand                             # joint over (beta, alpha)
        mx = lj.max(1, keepdims=True); w = np.exp(lj - mx); z = w.sum(1)
        logpost += np.log(z) + mx[:, 0]
        abar_given_b += (w * (pc - pn[None, :])).sum(1) / z                       # E[effect at this state | beta, data]
    p = np.exp(logpost - logpost.max()); p /= p.sum(); abar_given_b /= max(len(states), 1)
    cdf = np.cumsum(p); q = lambda x, a: float(x[np.searchsorted(cdf, a)])
    order = np.argsort(abar_given_b); ca = np.cumsum(p[order])
    qa = lambda a: float(abar_given_b[order][np.searchsorted(ca, a)])
    return {"beta": float((p * gb).sum()), "beta_lo90": q(gb, 0.05), "beta_hi90": q(gb, 0.95), "p_pos": float(p[gb > 0].sum()),
            "a_bar": float((p * abar_given_b).sum()), "a_lo90": qa(0.05), "a_hi90": qa(0.95)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--builds", required=True); ap.add_argument("--results", default="results")
    ap.add_argument("--runs", required=True); ap.add_argument("--instr", required=True); ap.add_argument("--cid", default="")
    ap.add_argument("--use-logged", type=int, default=1); ap.add_argument("--tau", type=float, default=1.5)
    ap.add_argument("--json-out", default="", help="write rows (for bit_active.py cands)"); a = ap.parse_args(); out_rows = []
    import bit_tree as BT
    eps = [e for e in load_episodes(a.runs.split(","), json.load(open(a.instr, encoding="utf-8"))) if not e["crashed"] and not e["has_replay"]]
    node_prior.tries = BT.build_tries(eps)
    data = collect([b for b in a.builds.split(",") if b], a.results)
    for cid, sts in sorted(data.items()):
        if a.cid and cid not in a.cid.split(","): continue
        states = []
        for key, st in sorted(sts.items()):
            if st["cn"] == 0 or st["nn"] == 0: continue
            st = dict(st); st["v0"] = min(max(node_prior(eps, st["eid"], st["k"]), 0.02), 0.98)
            if a.use_logged: st["nw"] += int(st["logged_won"]); st["nn"] += 1
            states.append(st)
        if not states: continue
        naive = np.mean([s["cw"] / s["cn"] - s["nw"] / s["nn"] for s in states])
        r = posterior(states, tau=a.tau)
        n_c = sum(s["cn"] for s in states); n_n = sum(s["nn"] for s in states)
        out_rows.append({"cid": cid, "states": len(states), "naive": float(naive), **r})
        print(f"{cid:28s} states {len(states):3d} (cand runs {n_c}, none runs {n_n})  naive a = {naive:+.3f}  |  pooled: a = {r['a_bar']:+.3f} "
              f"[{r['a_lo90']:+.3f},{r['a_hi90']:+.3f}]  beta = {r['beta']:+.2f} [{r['beta_lo90']:+.2f},{r['beta_hi90']:+.2f}]  P(beta>0) = {r['p_pos']:.3f}")

    if a.json_out: json.dump(out_rows, open(a.json_out, "w"), indent=1)


if __name__ == "__main__":
    main()
