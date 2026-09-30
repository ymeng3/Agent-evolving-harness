"""Phase 2 pilot scoring: per candidate whole delta vs bare (Discovery s1), per-edit gamma for compounds, judge for mechanism match; the six metrics."""
import json, os, re, sys
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_appworld"; DELTA = 3
def wins(tag):
    f = f"{R}/results/{tag}_seed1.json"; return (sum(json.load(open(f))["won"]), json.load(open(f))["api_errors"]) if os.path.exists(f) else (None, None)
base = wins("CH27_F0")[0]; cands = json.load(open(f"{R}/phase2/candidates.json"))
def judge(c):
    """gpt-4o: does the code actually intervene on the diagnosed mechanism (not just advice)?"""
    try: src = open(c["path"]).read()[:5000]
    except Exception: return None
    q = (f"Diagnosed failure mechanism: {c['mechanism']}\nDiagnosed address: {c.get('address')}\n\nPatch:\n```python\n{src}\n```\n\n"
         "Answer with one word: MATCHED if the patch's code actually intervenes on this mechanism through harness-executed state/code/control-flow or a precisely triggered prompt; PARTIAL if it addresses it only through generic advice; UNRELATED otherwise.")
    try: return A.gpt4o([{"role": "user", "content": q}], temperature=0, max_tokens=5).strip().split()[0].upper()
    except Exception: return None
rows = []
print(f"bare Discovery s1 = {base}\n{'candidate':44s} {'arm':5s} {'|C|':>3s} {'impls':22s} {'whole':>5s} {'d':>4s} {'err':>4s} {'judge':9s} per-edit gamma (ON - OFF) / verdict")
for c in cands:
    if not c["valid"]: rows.append({**c, "whole": None}); print(f"{c['pid']:44s} {c['arm']:5s} invalid: {c['why'][:50]}"); continue
    w, err = wins(c["pid"]); g = {}
    if w is not None and c["n_edits"] > 1:
        for e in c["edits"]:
            wo, eo = wins(f"{c['pid']}_off_{e['id']}")
            if wo is not None: g[e["id"]] = w - wo
    j = judge(c); c.update({"whole": w, "err": err, "d": (w - base) if w is not None else None, "gamma": g, "judge": j}); rows.append(c)
    verdict = ""
    if g:
        pos = [k for k, v in g.items() if v >= DELTA]; neg = [k for k, v in g.items() if v <= -DELTA]
        verdict = ("mixed" if pos and neg else "all>=0" if not neg else "has-harmful") + (" | decision-changing" if ((c["d"] or 0) < DELTA and pos) or ((c["d"] or 0) >= DELTA and neg) else "")
    print(f"{c['pid']:44s} {c['arm']:5s} {c['n_edits']:3d} {','.join(str(x) for x in c['impls'])[:22]:22s} {str(w):>5s} {str(c['d']):>4s} {str(err):>4s} {str(j):9s} {g} {verdict}")
for arm in ("naive", "fc"):
    v = [c for c in rows if c["arm"] == arm]; ok = [c for c in v if c["valid"] and c["whole"] is not None]
    print(f"\n== {arm}: proposed {len(v)} | ExecutableRate {sum(1 for c in v if c['valid'])}/{len(v)} | MechanismMatched {sum(1 for c in ok if c['judge']=='MATCHED')}/{len(ok)} (PARTIAL {sum(1 for c in ok if c['judge']=='PARTIAL')}) | PositiveCandidateRate(d>=+{DELTA}) {sum(1 for c in ok if (c['d'] or 0) >= DELTA)}/{len(ok)} | harmful(d<=-{DELTA}) {sum(1 for c in ok if (c['d'] or 0) <= -DELTA)} | NaturalCompoundRate {sum(1 for c in ok if c['n_edits']>1)}/{len(ok)} | prompt-only {sum(1 for c in ok if c['impls'] and all(i=='Prompt' for i in c['impls']))}")
    comp = [c for c in ok if c["n_edits"] > 1 and c["gamma"]]
    mixed = sum(1 for c in comp if any(v >= DELTA for v in c["gamma"].values()) and any(v <= -DELTA for v in c["gamma"].values()))
    dc = sum(1 for c in comp if ((c["d"] or 0) < DELTA and any(v >= DELTA for v in c["gamma"].values())) or ((c["d"] or 0) >= DELTA and any(v <= -DELTA for v in c["gamma"].values())))
    print(f"   compounds decomposed {len(comp)} | MixedValueRate {mixed}/{len(comp) or 1} | DecisionChangingRate {dc}/{len(comp) or 1}")
json.dump(rows, open(f"{R}/phase2/scored.json", "w"), indent=1)
