import json, collections
R = "/net/scratch/ymeng3/bos_appworld"; meta = json.load(open(f"{R}/pilot/meta.json")); tasks = list(meta)
res = {}
for pol in ("ctrl", "docfirst", "verify"):
    for s in (1, 2):
        try: d = json.load(open(f"{R}/results/PILOT_{pol}_seed{s}.json"))
        except Exception: print(pol, s, "missing"); continue
        res[(pol, s)] = {t: (w, G, sum(x["exec_error"] for x in tr if not x.get("replayed"))) for t, w, G, tr in zip(d["games"], d["won"], d["G"], d["traj"])}
print(f"{'policy':10s} seed  won/10  mean_G  new_exec_errors  per-task won")
for (pol, s), m in sorted(res.items()):
    print(f"{pol:10s} {s}     {sum(v[0] for v in m.values()):2d}/10   {sum(v[1] or 0 for v in m.values())/10:.2f}    {sum(v[2] for v in m.values()):3d}            {[int(m[t][0]) for t in tasks]}")
print("\nper task: F0 G | ctrl s1,s2 | docfirst s1,s2 | verify s1,s2  (won)")
for t in tasks:
    row = [f"{res[(p, s)][t][0] and 'W' or '.'}" if (p, s) in res else "?" for p in ("ctrl", "docfirst", "verify") for s in (1, 2)]
    print(f"  {t:12s} G0 {meta[t]['G_f0']:.2f} branch@{meta[t]['t_branch']:2d} | {' '.join(row[0:2])} | {' '.join(row[2:4])} | {' '.join(row[4:6])}")
any_ctrl = sum(any(res[(('ctrl'), s)][t][0] for s in (1, 2) if ('ctrl', s) in res) for t in tasks)
for p in ("docfirst", "verify"):
    anyp = sum(any(res[(p, s)][t][0] for s in (1, 2) if (p, s) in res) for t in tasks); print(f"{p}: tasks rescued in >=1 seed {anyp}/10 (control {any_ctrl}/10)")
