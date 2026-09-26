#!/usr/bin/env python3
"""$0 census: find natural FAILED compounds with 5-8 distinct executable semantic edits that could
host a credit-guided-salvage vs budget-matched-search comparison. No API calls, read-only."""
import json, glob, os, re, ast, itertools, hashlib, sys, collections, statistics as st
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag")
from b2_smoke import smoke
from kga_features import HOOKS
ROOT = "/net/scratch/ymeng3/bos_alfworld"; F0 = 35.82089552238806

def units(src):
    """Distinct REMOVABLE EXECUTABLE UNITS. A hook def = 1. A module constant = 1.
    A TEMPERATURE constant is NOT counted separately when retry_policy also sets temperature
    internally -- per the provenance finding, that is ONE two-site intervention, not two."""
    t = ast.parse(src)
    hooks = [n.name for n in t.body if isinstance(n, ast.FunctionDef) and n.name in HOOKS]
    consts = [n.targets[0].id for n in t.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("HISTORY_LENGTH", "TEMPERATURE")]
    internal_temp = bool(re.search(r"[\"']temperature[\"']\s*:", src))
    merged = []
    for c in consts:
        if c == "TEMPERATURE" and internal_temp and "retry_policy" in hooks:
            continue                      # merged into the retry_policy unit
        merged.append(c)
    return hooks + merged, (len(consts) - len(merged))

def drop(src, unit):
    if unit in HOOKS:
        t = ast.parse(src)
        keep = [n for n in t.body if not (isinstance(n, ast.FunctionDef) and n.name == unit)]
        return ast.unparse(ast.Module(body=keep, type_ignores=[])).strip()
    return "\n".join(l for l in src.splitlines() if not l.strip().startswith(unit)).strip()

def norm(s): return " ".join(re.sub(r"#.*", "", s).split())

# ---- measured bank, for whole-candidate evidence and subset leakage ----
measured = {}
for f in glob.glob(f"{ROOT}/results/*seed*.json"):
    try: d = json.load(open(f))
    except Exception: continue
    if "success_rate" not in d or not d.get("patch"): continue
    measured.setdefault(d["patch"], []).append(d["success_rate"] * 100)
bank = {}
for p in glob.glob(f"{ROOT}/patches*/**/*.py", recursive=True):
    try: bank.setdefault(norm(open(p).read().strip()), []).append(p)
    except Exception: pass

sm = json.load(open("/net/scratch/ymeng3/bos_screens/hag/smoke_all.json"))
rows = []
for r in sm:
    p = os.path.join(ROOT, r["path"])
    try: src = open(p).read().strip()
    except Exception: continue
    try: U, merged_away = units(src)
    except Exception: continue
    if len(U) < 5: continue
    q = measured.get(p)
    rows.append(dict(path=r["path"], full=p, group=r["group"], verdict=r["smoke_verdict"],
                     units=U, m=len(U), merged_away=merged_away, src=src,
                     seeds=len(q) if q else 0, delta=(st.mean(q) - F0) if q else None))
print("CANDIDATES WITH >=5 DISTINCT REMOVABLE UNITS: %d" % len(rows))
print("  by m:", dict(sorted(collections.Counter(r["m"] for r in rows).items())))
print("  by smoke verdict:", dict(collections.Counter(r["verdict"] for r in rows).items()))
print("  MEASURED at all: %d   | measured AND negative: %d" % (
    sum(1 for r in rows if r["seeds"]), sum(1 for r in rows if r["seeds"] and r["delta"] < 0)))
print("  (temperature constants merged into a retry unit in %d candidates)" % sum(1 for r in rows if r["merged_away"]))
print()
neg = [r for r in rows if r["seeds"] and r["delta"] < 0]
if neg:
    print("MEASURED FAILED COMPOUNDS WITH >=5 UNITS:")
    for r in sorted(neg, key=lambda x: x["delta"]):
        print("   %-50s m=%d seeds=%d delta %+.2f" % (r["path"][-50:], r["m"], r["seeds"], r["delta"]))
else:
    print("*** NO MEASURED FAILED COMPOUND HAS >=5 DISTINCT REMOVABLE UNITS. ***")
print()

# ---- full valid-lattice for PASS candidates with 5<=m<=8 ----
cand = [r for r in rows if r["verdict"] == "PASS" and 5 <= r["m"] <= 8]
print("Running full dependency/smoke lattice for %d PASS candidates (m in 5..8)..." % len(cand))
out = []
for r in cand:
    U = r["units"]; valid = 0; total = 0; leak = []
    for k in range(1, len(U)):                       # proper non-empty subsets
        for keep in itertools.combinations(U, k):
            s = r["src"]
            for d in [u for u in U if u not in keep]:
                try: s = drop(s, d)
                except Exception: s = None; break
            if s is None: continue
            total += 1
            try: v = smoke(s, "x")["smoke_verdict"]
            except Exception: v = "ERR"
            if v == "PASS":
                valid += 1
                hit = bank.get(norm(s))
                if hit and any(h in measured for h in hit): leak.append("+".join(keep))
    out.append(dict(r, valid=valid, total=total, leak=leak))
    print("   %-46s m=%d  valid %3d/%3d proper subsets  leaked %d" % (r["path"][-46:], r["m"], valid, total, len(leak)))
json.dump([{k: v for k, v in o.items() if k != "src"} for o in out],
          open("/net/scratch/ymeng3/bos_screens/hag/scaling_census.json", "w"), indent=1)
print("\nwritten: /net/scratch/ymeng3/bos_screens/hag/scaling_census.json")
