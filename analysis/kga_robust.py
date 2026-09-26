"""KG-A POST-HOC ROBUSTNESS. Registered as post-hoc: it CANNOT change the frozen verdict, which was
computed at seed 20260913 and stands. Two questions: (1) is the +2.5/+3.0pp stable across forest
seeds, (2) which C3 feature family carries it."""
import json, sys, collections, random
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag")
import kga_gate as G   # re-uses the frozen feature code and data build
from kga_rf_fast import rf_fit_predict
from kga_model import balanced_accuracy

D, gsize = G.D, G.gsize
y = [d["y"] for d in D]
folds = collections.defaultdict(list)
for i, d in enumerate(D): folds[d["group"]].append(i)

def oof(fn, seed):
    p = [0.0] * len(D)
    for k, te in folds.items():
        s = set(te); tr = [i for i in range(len(D)) if i not in s]
        T = G.c3_tables([D[i] for i in tr])
        Xtr = [fn(D[i], T) for i in tr]; ytr = [D[i]["y"] for i in tr]
        pr = rf_fit_predict(Xtr, ytr, [fn(D[i], T) for i in te], seed=seed)
        for j, i in enumerate(te): p[i] = pr[j]
    return balanced_accuracy(y, p)

F1 = lambda d, T: G.c1(d); F2 = lambda d, T: G.c2(d); F3 = lambda d, T: G.c3(d, T)
print("== SEED SENSITIVITY (frozen seed first) ==")
res = []
for s in (20260913, 1, 2, 3, 4):
    a, b, c = oof(F1, s), oof(F2, s), oof(F3, s)
    res.append((s, a, b, c))
    print("  seed %-9d C1 %.4f  C2 %.4f  C3 %.4f  | dBA_31 %+.4f  dBA_32 %+.4f" % (s, a, b, c, c - a, c - b))
d31 = [c - a for _, a, b, c in res]; d32 = [c - b for _, a, b, c in res]
print("  dBA_31 across seeds: min %+.4f max %+.4f | all positive: %s" % (min(d31), max(d31), all(x > 0 for x in d31)))
print("  dBA_32 across seeds: min %+.4f max %+.4f | all positive: %s" % (min(d32), max(d32), all(x > 0 for x in d32)))

# C3 has 11 features appended after C2's 70. Families, in append order:
FAM = {"hookset(2)": [0, 1], "hookpair(3)": [2, 3, 4], "editsha(3)": [5, 6, 7],
       "parentverdict(2)": [8, 9], "neverfired(1)": [10]}
print("\n== WHICH C3 FAMILY CARRIES IT (drop one family, frozen seed) ==")
base = oof(F3, 20260913)
print("  full C3 %.4f" % base)
for nm, ix in FAM.items():
    keep = [j for j in range(11) if j not in ix]
    fn = lambda d, T, keep=keep: G.c2(d) + [G.c3(d, T)[70:][j] for j in keep]
    v = oof(fn, 20260913)
    print("  drop %-18s C3 %.4f   (%+.4f vs full)" % (nm, v, v - base))
