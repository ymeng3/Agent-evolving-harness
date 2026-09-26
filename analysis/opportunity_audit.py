#!/usr/bin/env python3
"""$0 opportunity audit. Three quantities:
 A  invalid-counterfactual prevalence  (well powered: every archive candidate with m>=2)
 B  within-candidate salvage headroom  H_within = max_{S subset C} Q(S) - Q(C)   (only where measured)
 C  between-candidate selection headroom H_between = max_g Q - mean_g Q          (measured groups)
No API calls."""
import json, glob, os, sys, collections, statistics as st
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag")
from b2_smoke import smoke
from scaling_census import units, drop
ROOT = "/net/scratch/ymeng3/bos_alfworld"; F0 = 35.82089552238806

# ---------- A: invalid single-unit counterfactuals, whole archive ----------
sm = json.load(open("/net/scratch/ymeng3/bos_screens/hag/smoke_all.json"))
tot = bad = 0; per_cand = []; by_m = collections.defaultdict(lambda: [0, 0]); causes = collections.Counter()
for r in sm:
    if r["smoke_verdict"] != "PASS":      # only ablate compounds that are themselves valid
        continue
    src = open(os.path.join(ROOT, r["path"])).read().strip()
    try: U, _ = units(src)
    except Exception: continue
    if len(U) < 2: continue
    n_bad = 0
    for u in U:
        try: s = drop(src, u)
        except Exception: continue
        tot += 1; by_m[len(U)][0] += 1
        v = smoke(s, "x")
        if v["smoke_verdict"] != "PASS":
            bad += 1; n_bad += 1; by_m[len(U)][1] += 1
            for h in v.get("crashed_hooks", []): causes["CRASH:" + h] += 1
            for h in v.get("never_invoked_hooks", []): causes["never_fired:" + h] += 1
            for h in v.get("no_effect_hooks", []): causes["no_effect:" + h] += 1
    per_cand.append((r["path"], len(U), n_bad))
print("=== A. INVALID SINGLE-UNIT COUNTERFACTUALS (valid compounds, m>=2) ===")
print("  compounds audited: %d | single-unit ablations: %d | INVALID: %d (%.1f%%)" % (len(per_cand), tot, bad, 100*bad/max(tot,1)))
print("  compounds with >=1 invalid ablation: %d of %d (%.1f%%)" % (
    sum(1 for _,_,b in per_cand if b), len(per_cand), 100*sum(1 for _,_,b in per_cand if b)/max(len(per_cand),1)))
print("  by m (ablations, invalid, rate):")
for m in sorted(by_m): print("     m=%d  %5d  %4d  %.1f%%" % (m, by_m[m][0], by_m[m][1], 100*by_m[m][1]/by_m[m][0]))
print("  top causes:", dict(causes.most_common(8)))
json.dump({"tot": tot, "bad": bad, "per_cand": per_cand}, open("/net/scratch/ymeng3/bos_screens/hag/oppA.json", "w"))

# ---------- C: between-candidate selection headroom, from measured groups ----------
meas = collections.defaultdict(list)
for f in glob.glob(f"{ROOT}/results/*seed*.json"):
    try: d = json.load(open(f))
    except Exception: continue
    if "success_rate" not in d or not d.get("patch"): continue
    meas[d["patch"]].append(d["success_rate"] * 100)
grp = collections.defaultdict(list)
for p, v in meas.items():
    rel = os.path.relpath(p, ROOT); parts = rel.split("/")
    g = parts[1] if len(parts) > 2 else parts[0]
    grp[g].append((os.path.basename(p), st.mean(v) - F0, len(v)))
print()
print("=== C. BETWEEN-CANDIDATE SELECTION HEADROOM (measured generation groups, n>=3) ===")
print("  %-22s %3s %8s %8s %9s" % ("group", "n", "max", "mean", "H_between"))
H = []
for g, v in sorted(grp.items()):
    if len(v) < 3: continue
    mx = max(x[1] for x in v); mn = st.mean(x[1] for x in v)
    H.append(mx - mn)
    print("  %-22s %3d %+8.2f %+8.2f %+9.2f" % (g, len(v), mx, mn, mx - mn))
if H: print("  --> H_between: median %+.2f pp, mean %+.2f pp over %d groups" % (st.median(H), st.mean(H), len(H)))
