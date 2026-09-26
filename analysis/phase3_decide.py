"""Phase 3 decisions. usage: phase3_decide.py cands | unit KEY N  -> prints JSON {decision, d, n, halves}"""
import json, os, sys
R = "/net/scratch/ymeng3/bos_alfworld"; P3 = f"{R}/patches_p3"
def wm(tag):
    f = f"{R}/results/{tag}_seed1.json"
    if not os.path.exists(f): return None
    d = json.load(open(f)); return dict(zip(d.get("games_actual") or d["games"], [int(w) for w in d["won"]]))
def paired(on, off):
    gs = [g for g in on if g in off]; d = [on[g] - off[g] for g in gs]; return gs, d
if sys.argv[1] == "cands":
    out = {}
    for key in ("r6", "n5", "r2"):
        on, par = wm(f"P3C_{key}"), wm(f"P3P_{key}")
        if not on or not par: out[key] = {"decision": "missing"}; continue
        gs, d = paired(on, par); out[key] = {"C_wins": sum(on.values()), "parent_wins": sum(par.values()), "paired_d": sum(d), "n": len(gs), "decompose": sum(d) >= 2}
    print(json.dumps(out)); json.dump(out, open(f"{P3}/cands_decision.json", "w"), indent=1)
else:
    key, n = sys.argv[2], int(sys.argv[3]); U = json.load(open(f"{P3}/units.json"))[key]
    on = wm(U["Ctag"]); off = wm(f"P3OFF_{key.replace(':','_')}_n{n}") if U["kind"] == "global" else wm(f"PL_p3_{key.replace(':','_')}_OFF_rep1")
    if not on or not off: print(json.dumps({"decision": "missing"})); sys.exit()
    gs, d = paired(on, off); h = len(d) // 2; s1, s2 = sum(d[:h]), sum(d[h:]); D = sum(d)
    stable = (s1 > 0 and s2 > 0) or (s1 < 0 and s2 < 0)
    if abs(D) >= 3 and stable: dec = "helpful" if D > 0 else "harmful"; stop = True
    elif len(d) >= 48: dec = "helpful" if D >= 3 else "harmful" if D <= -3 else "near-zero/uncertain"; stop = True
    else: dec = "continue"; stop = False
    print(json.dumps({"decision": dec, "stop": stop, "d": D, "n": len(d), "halves": [s1, s2], "on": sum(on[g] for g in gs), "off": sum(off[g] for g in gs)}))
