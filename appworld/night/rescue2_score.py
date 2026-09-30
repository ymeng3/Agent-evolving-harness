import json, os, collections
R = "/net/scratch/ymeng3/bos_appworld"; meta = json.load(open(f"{R}/night/meta.json")); tasks = list(meta); res = {}
for pol in ("ctrl", "h0", "h1", "h2"):
    for s in (1, 2):
        f = f"{R}/results/RS2_{pol}_seed{s}.json"
        if os.path.exists(f): d = json.load(open(f)); res[(pol, s)] = dict(zip(d["games"], zip(d["won"], d["G"])))
print(f"{'arm':6s} seed  won/{len(tasks)}  meanG")
for (pol, s), m in sorted(res.items()): print(f"{pol:6s} {s}     {sum(v[0] for v in m.values()):3d}      {sum((v[1] or 0) for v in m.values())/len(m):.2f}")
def any_won(pol): return sum(any(res[(pol, s)][t][0] for s in (1, 2) if (pol, s) in res and t in res[(pol, s)]) for t in tasks)
print("tasks rescued in >=1 seed: control", any_won("ctrl"), "| any strategy:", sum(any(res[(p, s)][t][0] for p in ("h0", "h1", "h2") for s in (1, 2) if (p, s) in res and t in res[(p, s)]) for t in tasks), "| per strategy:", {p: any_won(p) for p in ("h0", "h1", "h2")})
print("per task [ctrl s1 s2 | h0 | h1 | h2] (W=won):")
for t in tasks:
    row = "".join(("W" if res[(p, s)][t][0] else ".") if (p, s) in res and t in res[(p, s)] else "?" for p in ("ctrl", "h0", "h1", "h2") for s in (1, 2))
    print(f"  {t:12s} G0 {meta[t]['G_f0'] or 0:.2f} branch@{meta[t]['t_branch']:2d} {row[:2]} | {row[2:4]} | {row[4:6]} | {row[6:8]}  {meta[t]['instruction'][:60]}")
