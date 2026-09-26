"""KG-A models, hand-rolled, pure Python, deterministic. Frozen per KGA_PREREG.md sha ec3fa570cfeabc8b."""
import math, random

# ---------------- random forest (PRIMARY) ----------------
def _thresholds(col, k=8):
    v = sorted(set(col))
    if len(v) <= 1: return []
    if len(v) <= k: return [(v[i] + v[i+1]) / 2 for i in range(len(v) - 1)]
    qs = [v[int(len(v) * (i + 1) / (k + 1))] for i in range(k)]
    out = []
    for q in sorted(set(qs)):
        if q > v[0]: out.append(q)
    return out

def _gini(pos, n):
    if n == 0: return 0.0
    p = pos / n
    return 2 * p * (1 - p)

def _build(X, y, idx, feats, thr, depth, max_depth, min_leaf, rng):
    pos = sum(y[i] for i in idx); n = len(idx)
    leaf = {"leaf": pos / n if n else 0.5}
    if depth >= max_depth or n < 2 * min_leaf or pos == 0 or pos == n: return leaf
    best = None
    for f in rng.sample(feats, min(len(feats), _build.max_features)):
        for t in thr[f]:
            lp = ln = rp = rn = 0
            for i in idx:
                if X[i][f] <= t: ln += 1; lp += y[i]
                else: rn += 1; rp += y[i]
            if ln < min_leaf or rn < min_leaf: continue
            sc = (ln * _gini(lp, ln) + rn * _gini(rp, rn)) / n
            if best is None or sc < best[0]: best = (sc, f, t)
    if best is None: return leaf
    _, f, t = best
    L = [i for i in idx if X[i][f] <= t]; R = [i for i in idx if X[i][f] > t]
    return {"f": f, "t": t,
            "L": _build(X, y, L, feats, thr, depth + 1, max_depth, min_leaf, rng),
            "R": _build(X, y, R, feats, thr, depth + 1, max_depth, min_leaf, rng)}

def _pred1(node, x):
    while "leaf" not in node: node = node["L"] if x[node["f"]] <= node["t"] else node["R"]
    return node["leaf"]

def rf_fit_predict(Xtr, ytr, Xte, n_trees=40, max_depth=4, min_leaf=5, max_features=6, seed=20260913):
    if not Xtr: return [0.5] * len(Xte)
    p = len(Xtr[0]); feats = list(range(p))
    thr = {f: _thresholds([r[f] for r in Xtr]) for f in feats}
    _build.max_features = max_features
    rng = random.Random(seed)
    out = [0.0] * len(Xte)
    for b in range(n_trees):
        idx = [rng.randrange(len(Xtr)) for _ in Xtr]
        tree = _build(Xtr, ytr, idx, feats, thr, 0, max_depth, min_leaf, rng)
        for j, x in enumerate(Xte): out[j] += _pred1(tree, x)
    return [o / n_trees for o in out]

# ---------------- L2 logistic regression (SECONDARY) ----------------
def lr_fit_predict(Xtr, ytr, Xte, lam=1.0, steps=300, lr=0.5):
    if not Xtr: return [0.5] * len(Xte)
    n, p = len(Xtr), len(Xtr[0])
    mu = [sum(r[f] for r in Xtr) / n for f in range(p)]
    sd = [math.sqrt(sum((r[f] - mu[f]) ** 2 for r in Xtr) / n) or 1.0 for f in range(p)]
    Z = [[(r[f] - mu[f]) / sd[f] for f in range(p)] for r in Xtr]
    w = [0.0] * p; b = 0.0
    for _ in range(steps):
        gw = [0.0] * p; gb = 0.0
        for i in range(n):
            z = b + sum(w[f] * Z[i][f] for f in range(p))
            e = 1 / (1 + math.exp(-max(-30, min(30, z)))) - ytr[i]
            gb += e
            for f in range(p): gw[f] += e * Z[i][f]
        b -= lr * gb / n
        for f in range(p): w[f] -= lr * (gw[f] / n + lam * w[f] / n)
    out = []
    for r in Xte:
        z = b + sum(w[f] * (r[f] - mu[f]) / sd[f] for f in range(p))
        out.append(1 / (1 + math.exp(-max(-30, min(30, z)))))
    return out

# ---------------- metrics ----------------
def balanced_accuracy(y, p, thr=0.5):
    tp = sum(1 for a, b in zip(y, p) if a == 1 and b >= thr); fn = sum(1 for a, b in zip(y, p) if a == 1 and b < thr)
    tn = sum(1 for a, b in zip(y, p) if a == 0 and b < thr); fp = sum(1 for a, b in zip(y, p) if a == 0 and b >= thr)
    se = tp / (tp + fn) if tp + fn else 0.0
    sp = tn / (tn + fp) if tn + fp else 0.0
    return (se + sp) / 2

def auroc(y, p):
    pairs = sorted(zip(p, y)); pos = sum(y); neg = len(y) - pos
    if not pos or not neg: return float("nan")
    r = {}; i = 0; ranks = [0.0] * len(pairs)
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]: j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1): ranks[k] = avg
        i = j + 1
    s = sum(rk for rk, (_, yy) in zip(ranks, pairs) if yy == 1)
    return (s - pos * (pos + 1) / 2) / (pos * neg)

def brier(y, p): return sum((a - b) ** 2 for a, b in zip(y, p)) / len(y)
