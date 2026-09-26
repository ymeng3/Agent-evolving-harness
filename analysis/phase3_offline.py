"""Phase 3 offline replay (2026-09-26): paired per-game ON/OFF outcomes for each component, revealed in batches.
Strategies: FIXED (all n), PAIRED+ADAPTIVE (across-component allocation by flip-probability), ROUTED (local CF@32 first for
fallback/retry/parse, then adaptive global for the unclear), PRM-PRIORITY (adaptive, first batches ordered by |PRM dV|).
Truth = decision from ALL paired data (delta=3pp). Cost unit = OFF episodes (ON pass shared per C); local CF branch = 0.74 ep."""
import json, glob, os, sys, math, random, statistics as st
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag"); from p2_components import C
R = "/net/scratch/ymeng3/bos_alfworld"; DELTA = 3.0; MINB, BATCH = 16, 8; random.seed(0)
idx = {}
for f in glob.glob(f"{R}/results/*_seed*.json"):
    try: d = json.load(open(f))
    except Exception: continue
    if "won" not in d or d.get("n_games") not in (48, 96): continue
    idx.setdefault(d.get("patch"), []).append(d)
def won_map(d): return dict(zip(d.get("games_actual") or d["games"], [int(w) for w in d["won"]]))
comp = {}
for name, src, kind, cp, op, g in C:
    pairs = []
    for a in idx.get(cp, []):
        for b in idx.get(op, []):
            if a["seed"] == b["seed"] and a["n_games"] == b["n_games"] and a.get("manifest") == b.get("manifest") and a.get("model") == b.get("model"):
                wa, wb = won_map(a), won_map(b); gs = [x for x in (a.get("games_actual") or a["games"]) if x in wb]
                pairs.append([(wa[x], wb[x]) for x in gs])
    if not pairs: continue
    seen = set(); uniq = []
    for p in pairs:
        k = tuple(p)
        if k not in seen: seen.add(k); uniq.append(p)
    comp[name] = {"kind": kind, "gamma": g, "pairs": uniq}
print(f"components with paired full-pass data: {len(comp)} / {len(C)}")
# variance check: paired vs independent
vp, vi = [], []
for k, v in comp.items():
    for p in v["pairs"]:
        d = [a - b for a, b in p]; on = [a for a, b in p]; off = [b for a, b in p]
        vp.append(st.pvariance(d)); vi.append(st.pvariance(on) + st.pvariance(off))
print(f"Var(paired diff) / Var(independent diff): {st.mean(vp)/st.mean(vi):.2f}  (over {len(vp)} pair-sets)")
def cls(m): return "helpful" if m > DELTA else "harmful" if m < -DELTA else "neutral"
truth = {}
for k, v in comp.items():
    allp = [x for p in v["pairs"] for x in p]; truth[k] = cls(100 * st.mean(a - b for a, b in allp))
print("truth:", {t: sum(1 for k in truth if truth[k] == t) for t in ("helpful", "harmful", "neutral")})
# local CF per-game diffs (Phase 2) for routed strategy
cf = {}
for name, src, kind, cp, op, g in C:
    s = "p2_" + name.replace(" ", "_"); f = f"{R}/results/PL_{s}_OFF_rep1_seed1.json"; meta = f"{R}/probeL/{s}_meta.json"
    if not (os.path.exists(f) and os.path.exists(meta)): continue
    d = json.load(open(f)); M = json.load(open(meta)); order = [l.strip() for l in open(f"{R}/probeL/{s}_manifest.txt") if l.strip()]
    off = won_map(d); cf[name] = [M[x]["won_on_original"] - off[x] for x in order if x in off]
prm = json.load(open(f"{R}/hag_prm_scores.json")) if os.path.exists(f"{R}/hag_prm_scores.json") else {}
def stream(k, rep):
    """one paired sequence (use pair-set rep, shuffled with a fixed seed) as a list of diffs"""
    p = comp[k]["pairs"][rep % len(comp[k]["pairs"])]; d = [a - b for a, b in p]; rr = random.Random(rep); rr.shuffle(d); return d
def flip_prob(d):
    n = len(d); m = 100 * st.mean(d); se = 100 * (st.pstdev(d) / math.sqrt(n) if n > 1 else 1.0); se = max(se, 1e-6)
    # probability that the true mean lies on the other side of the nearest decision boundary
    if m > DELTA: z = (m - DELTA) / se
    elif m < -DELTA: z = (-DELTA - m) / se
    else: z = min(DELTA - m, m + DELTA) / se
    return 0.5 * math.erfc(z / math.sqrt(2))
def run_adaptive(keys, rep, budget_cap, order_key=None, pre=None, stop_p=0.05):
    """returns decisions, cost (OFF episodes). pre = {k: (decision, cost)} already decided by local CF."""
    used = {k: 0 for k in keys}; dec = {}; cost = 0.0
    if pre:
        for k, (dk, ck) in pre.items(): dec[k] = dk; cost += ck
    active = [k for k in keys if k not in dec]; S = {k: stream(k, rep) for k in active}
    for k in active: used[k] = min(MINB, len(S[k])); cost += used[k]
    order = sorted(active, key=order_key) if order_key else active
    while True:
        cand = [k for k in order if k not in dec]
        if not cand: break
        # finalise those that are confident or exhausted
        for k in cand:
            d = S[k][:used[k]]
            if flip_prob(d) < stop_p or used[k] >= min(budget_cap, len(S[k])): dec[k] = cls(100 * st.mean(d))
        cand = [k for k in order if k not in dec]
        if not cand: break
        k = max(cand, key=lambda q: flip_prob(S[q][:used[q]])) if order_key is None else cand[0]
        add = min(BATCH, len(S[k]) - used[k]); used[k] += add; cost += add
    return dec, cost, used
def score(dec): return sum(dec[k] == truth[k] for k in dec) / len(dec)
keys = list(comp); REPS = 5; rows = {}
for rep in range(REPS):
    # FIXED: all n
    dec = {k: cls(100 * st.mean(stream(k, rep))) for k in keys}; cost = sum(len(stream(k, rep)) for k in keys); rows.setdefault("fixed all-n", []).append((score(dec), cost))
    # fixed 48
    dec = {k: cls(100 * st.mean(stream(k, rep)[:48])) for k in keys}; cost = sum(min(48, len(stream(k, rep))) for k in keys); rows.setdefault("fixed 48", []).append((score(dec), cost))
    # paired adaptive
    dec, cost, used = run_adaptive(keys, rep, 96); rows.setdefault("paired+adaptive", []).append((score(dec), cost))
    # routed: local CF@32 first for local-kind components
    pre = {}
    for k in keys:
        if comp[k]["kind"] in ("fallback", "retry", "parse") and k in cf:
            d = cf[k][:32]; m = 100 * st.mean(d); se = 100 * st.pstdev(d) / math.sqrt(len(d))
            c = 0.74 * len(d)
            if m - 2 * se > DELTA: pre[k] = ("helpful", c)
            elif m + 2 * se < -DELTA: pre[k] = ("harmful", c)
            else: pre[k] = None
    unclear_cost = sum(0.74 * 32 for k, v in pre.items() if v is None); pre = {k: v for k, v in pre.items() if v}
    dec, cost, used = run_adaptive(keys, rep, 96, pre=pre); rows.setdefault("routed (localCF->adaptive)", []).append((score(dec), cost + unclear_cost))
    # PRM priority: process components in order of |dV| desc (highest first gets batches until decided)
    if prm:
        dec, cost, used = run_adaptive(keys, rep, 96, order_key=lambda q: -abs(prm.get(q, {}).get("dV_promise", 0) or 0)); rows.setdefault("PRM-priority adaptive", []).append((score(dec), cost))
print(f"\n{'strategy':28s} {'decision acc':>12s} {'cost (OFF episodes)':>20s}  {'vs fixed all-n':>14s}")
base = st.mean(c for a, c in rows["fixed all-n"])
for k, v in rows.items(): print(f"{k:28s} {st.mean(a for a,c in v):12.2f} {st.mean(c for a,c in v):20.0f}  {100*st.mean(c for a,c in v)/base:13.0f}%")
print("\nper-component (rep 0, paired+adaptive): truth / decided / pairs used")
dec, cost, used = run_adaptive(keys, 0, 96)
for k in keys: print(f"  {k:18s} {comp[k]['kind']:8s} truth {truth[k]:8s} dec {dec[k]:8s} n {used[k]}")
