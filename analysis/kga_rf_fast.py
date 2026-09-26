"""Binned implementation of the SAME frozen forest (40 trees, depth 4, min_leaf 5, max_features 6,
quantile thresholds <=8 per feature, seed 20260913). Binning IS the frozen threshold spec; this only
replaces per-row scans with histogram accumulation. Self-tested against the reference implementation."""
import random

def _bins(col, k=8):
    v = sorted(set(col))
    if len(v) <= 1: return []
    if len(v) <= k: return [(v[i] + v[i+1]) / 2 for i in range(len(v) - 1)]
    qs = sorted({v[int(len(v) * (i + 1) / (k + 1))] for i in range(k)})
    return [q for q in qs if q > v[0]]

def _binize(X, cuts):
    out = []
    for r in X:
        row = []
        for f, cs in enumerate(cuts):
            x = r[f]; b = 0
            for c in cs:
                if x > c: b += 1
                else: break
            row.append(b)
        out.append(row)
    return out

def _gini(pos, n): 
    if not n: return 0.0
    p = pos / n; return 2 * p * (1 - p)

def _grow(B, y, idx, nb, depth, md, ml, mf, rng, p):
    n = len(idx); pos = sum(y[i] for i in idx)
    if depth >= md or n < 2 * ml or pos == 0 or pos == n:
        return ("L", pos / n if n else 0.5)
    best = None
    for f in rng.sample(range(p), min(p, mf)):
        k = nb[f]
        if k <= 1: continue
        cn = [0] * k; cp = [0] * k
        for i in idx:
            b = B[i][f]; cn[b] += 1; cp[b] += y[i]
        ln = lp = 0
        for b in range(k - 1):
            ln += cn[b]; lp += cp[b]
            rn = n - ln; rp = pos - lp
            if ln < ml or rn < ml: continue
            sc = (ln * _gini(lp, ln) + rn * _gini(rp, rn)) / n
            if best is None or sc < best[0]: best = (sc, f, b)
    if best is None: return ("L", pos / n)
    _, f, b = best
    Li = [i for i in idx if B[i][f] <= b]; Ri = [i for i in idx if B[i][f] > b]
    return ("N", f, b, _grow(B, y, Li, nb, depth + 1, md, ml, mf, rng, p),
                        _grow(B, y, Ri, nb, depth + 1, md, ml, mf, rng, p))

def _pred(t, x):
    while t[0] == "N": t = t[3] if x[t[1]] <= t[2] else t[4]
    return t[1]

def rf_fit_predict(Xtr, ytr, Xte, n_trees=40, max_depth=4, min_leaf=5, max_features=6, seed=20260913):
    if not Xtr: return [0.5] * len(Xte)
    p = len(Xtr[0])
    cuts = [_bins([r[f] for r in Xtr]) for f in range(p)]
    nb = [len(c) + 1 for c in cuts]
    Btr = _binize(Xtr, cuts); Bte = _binize(Xte, cuts)
    rng = random.Random(seed)
    out = [0.0] * len(Bte)
    for _ in range(n_trees):
        idx = [rng.randrange(len(Btr)) for _ in Btr]
        t = _grow(Btr, ytr, idx, nb, 0, max_depth, min_leaf, max_features, rng, p)
        for j, x in enumerate(Bte): out[j] += _pred(t, x)
    return [o / n_trees for o in out]
