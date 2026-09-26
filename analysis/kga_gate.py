"""KG-A GATE. Frozen per KGA_PREREG.md sha ec3fa570cfeabc8b. Zero API calls."""
import json, sys, math, random, collections, itertools, os
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag")
from kga_features import own_source_features, HOOKS
from kga_rf_fast import rf_fit_predict
from kga_model import lr_fit_predict, balanced_accuracy, auroc, brier

ROOT = "/net/scratch/ymeng3/bos_alfworld"
rows = json.load(open("/net/scratch/ymeng3/bos_screens/hag/smoke_all.json"))
dag = json.load(open("/net/scratch/ymeng3/bos_screens/lineage/provenance_dag.json"))

# ---- provenance structure (NO runtime outcome of any candidate) ----
byid = {n["id"]: n for n in dag["nodes"]}
path2id = {n["path"]: n["id"] for n in dag["nodes"] if n.get("path")}
parent = {}; contains = collections.defaultdict(set)
for e in dag["edges"]:
    if e["rel"] == "descends-from": parent.setdefault(e["src"], e["dst"])
    if e["rel"] == "contains": contains[e["src"]].add(e["dst"])
kids = collections.Counter(parent.values())

D = []
for r in rows:
    src = open(os.path.join(ROOT, r["path"])).read()
    f, shas = own_source_features(src)
    y = 1 if r["smoke_verdict"] == "PASS" else 0
    nid = path2id.get(r["path"])
    pid = parent.get(nid) if nid else None
    depth = 0; a = nid
    seen = set()
    while a in parent and a not in seen:
        seen.add(a); a = parent[a]; depth += 1
    hs = frozenset(h for h in HOOKS if f["has_" + h] == 1.0)
    D.append(dict(path=r["path"], group=r["group"], y=y, c1=f, shas=shas, nid=nid, pid=pid,
                  depth=depth, hookset=hs,
                  pairs=frozenset(frozenset(p) for p in itertools.combinations(sorted(hs), 2)),
                  nedits=len(contains.get(nid, ())) if nid else 0,
                  nsib=kids.get(pid, 0) if pid else 0,
                  neverfired=bool(r.get("never_invoked_hooks"))))
gsize = collections.Counter(d["group"] for d in D)
gidx = collections.defaultdict(int)
for d in sorted(D, key=lambda x: x["path"]):
    d["idx"] = gidx[d["group"]]; gidx[d["group"]] += 1

C1KEYS = list(D[0]["c1"].keys())
def c1(d): return [d["c1"][k] for k in C1KEYS]

def c2(d):
    ph = byid.get(d["pid"], {}) if d["pid"] else {}
    pset = frozenset()
    if d["pid"]:
        for row in D:
            if row["nid"] == d["pid"]: pset = row["hookset"]; break
    inter = len(d["hookset"] & pset); uni = len(d["hookset"] | pset)
    return c1(d) + [float(gsize[d["group"]]), float(d["idx"]), float(d["idx"]) / max(gsize[d["group"]], 1),
                    float(d["depth"]), float(d["nedits"]), float(d["nsib"]),
                    1.0 if d["pid"] else 0.0, (inter / uni) if uni else 0.0,
                    1.0 if "drop" in d["group"].lower() else 0.0,
                    1.0 if "whole" in d["group"].lower() else 0.0]

def c3_tables(train):
    """Built from TRAINING rows only. This is where other candidates' RUNTIME LABELS enter."""
    hs = collections.defaultdict(lambda: [0, 0]); pr = collections.defaultdict(lambda: [0, 0])
    sh = collections.defaultdict(lambda: [0, 0]); nf = collections.defaultdict(lambda: [0, 0])
    pv = {}
    for d in train:
        hs[d["hookset"]][0] += 1; hs[d["hookset"]][1] += d["y"]
        for p in d["pairs"]:
            pr[p][0] += 1; pr[p][1] += d["y"]
            nf[p][0] += 1; nf[p][1] += int(d["neverfired"])
        for s in d["shas"].values():
            sh[s][0] += 1; sh[s][1] += d["y"]
        if d["nid"]: pv[d["nid"]] = d["y"]
    return hs, pr, sh, nf, pv

def c3(d, T):
    hs, pr, sh, nf, pv = T
    a = hs.get(d["hookset"], [0, 0])
    prs = [pr[p] for p in d["pairs"] if p in pr]
    nfs = [nf[p] for p in d["pairs"] if p in nf]
    shs = [sh[s] for s in d["shas"].values() if s in sh]
    def rate(v, dflt=0.5): return (v[1] / v[0]) if v[0] else dflt
    return c2(d) + [
        rate(a), float(a[0]),
        (sum(rate(x) for x in prs) / len(prs)) if prs else 0.5,
        min((rate(x) for x in prs), default=0.5),
        float(sum(x[0] for x in prs)),
        (sum(rate(x) for x in shs) / len(shs)) if shs else 0.5,
        float(sum(x[0] for x in shs)), float(len(shs)),
        (pv[d["pid"]] if d["pid"] in pv else 0.5),
        1.0 if d["pid"] in pv else 0.0,
        max((rate(x, 0.0) for x in nfs), default=0.0),
    ]

def run(fold_key, model, tag):
    folds = collections.defaultdict(list)
    for i, d in enumerate(D): folds[fold_key(d, i)].append(i)
    oof = {c: [0.0] * len(D) for c in ("C1", "C2", "C3")}
    for k, te in folds.items():
        tr = [i for i in range(len(D)) if i not in set(te)]
        train = [D[i] for i in tr]; T = c3_tables(train)
        for c, fn in (("C1", lambda d: c1(d)), ("C2", c2), ("C3", lambda d: c3(d, T))):
            Xtr = [fn(D[i]) for i in tr]; ytr = [D[i]["y"] for i in tr]
            p = model(Xtr, ytr, [fn(D[i]) for i in te])
            for j, i in enumerate(te): oof[c][i] = p[j]
    y = [d["y"] for d in D]
    res = {c: dict(BA=balanced_accuracy(y, oof[c]), AUROC=auroc(y, oof[c]), Brier=brier(y, oof[c])) for c in oof}
    # group bootstrap on the 61 groups
    gmap = collections.defaultdict(list)
    for i, d in enumerate(D): gmap[d["group"]].append(i)
    gs = list(gmap); rng = random.Random(20260913)
    b31 = []; b32 = []
    for _ in range(5000):
        pick = [rng.choice(gs) for _ in gs]
        idx = [i for g in pick for i in gmap[g]]
        yy = [y[i] for i in idx]
        if len(set(yy)) < 2: continue
        ba = {c: balanced_accuracy(yy, [oof[c][i] for i in idx]) for c in oof}
        b31.append(ba["C3"] - ba["C1"]); b32.append(ba["C3"] - ba["C2"])
    b31.sort(); b32.sort()
    def ci(b): return (b[int(.025 * len(b))], b[int(.975 * len(b))])
    res["dBA_31"] = dict(point=res["C3"]["BA"] - res["C1"]["BA"], ci=ci(b31))
    res["dBA_32"] = dict(point=res["C3"]["BA"] - res["C2"]["BA"], ci=ci(b32))
    res["tag"] = tag
    return res

OUT = {}
OUT["PRIMARY_leave_one_GROUP_out_RF"] = run(lambda d, i: d["group"], rf_fit_predict, "primary")
OUT["SECONDARY_leave_one_CANDIDATE_out_RF"] = run(lambda d, i: i, rf_fit_predict, "loo-leaky")
OUT["SECONDARY_leave_one_GROUP_out_LOGISTIC"] = run(lambda d, i: d["group"], lr_fit_predict, "logistic")
OUT["meta"] = dict(n=len(D), pos=sum(d["y"] for d in D), groups=len(gsize),
                   n_feat=dict(C1=len(c1(D[0])), C2=len(c2(D[0])), C3=len(c3(D[0], c3_tables(D)))))
json.dump(OUT, open("/net/scratch/ymeng3/bos_screens/hag/kga_result.json", "w"), indent=1)
for k, v in OUT.items():
    if k == "meta": print("META", v); continue
    print("\n== %s ==" % k)
    for c in ("C1", "C2", "C3"):
        print("   %-3s BA %.4f  AUROC %.4f  Brier %.4f" % (c, v[c]["BA"], v[c]["AUROC"], v[c]["Brier"]))
    print("   dBA_31 %+.4f CI95 [%+.4f, %+.4f]" % (v["dBA_31"]["point"], *v["dBA_31"]["ci"]))
    print("   dBA_32 %+.4f CI95 [%+.4f, %+.4f]" % (v["dBA_32"]["point"], *v["dBA_32"]["ci"]))
