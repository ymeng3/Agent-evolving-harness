import json,collections,sys
R="/net/scratch/ymeng3/bos_alfworld"; meta=json.load(open(f"{R}/fd/meta.json")); tags=["FD_ctrl"]+[f"FD_hint{k}" for k in range(4)]
res={}
for t in tags:
    try: d=json.load(open(f"{R}/results/{t}_seed1.json")); res[t]={g:int(w) for g,w in zip(d["games_actual"],d["won"])}
    except Exception as e: print(t,"missing")
games=list(meta); print(f"failures {len(games)}", collections.Counter(m['class'] for m in meta.values()))
print(f"{'pass':10s} {'rescued':>8s} " + " ".join(f"{c:>13s}" for c in ("never_picked","picked","processed")))
for t in res:
    by=collections.defaultdict(lambda:[0,0])
    for g in games:
        if g in res[t]: by[meta[g]["class"]][0]+=res[t][g]; by[meta[g]["class"]][1]+=1
    print(f"{t:10s} {sum(res[t].values()):3d}/{len(res[t]):<3d}  " + " ".join(f"{by[c][0]:3d}/{by[c][1]:<3d}      " for c in ("never_picked","picked","processed")))
if "FD_ctrl" in res:
    anyh=sum(any(res[t].get(g,0) for t in res if t!="FD_ctrl") for g in games); ctrl=sum(res["FD_ctrl"].values())
    print(f"games rescued by AT LEAST ONE alternative: {anyh}/{len(games)} | control: {ctrl}/{len(games)}")
    per=[(g.split('/')[-3][:40], meta[g]['class'], [res[t].get(g,0) for t in tags if t in res]) for g in games]
    print("per-game [ctrl,h0,h1,h2,h3]:"); [print("  ",p) for p in per]
