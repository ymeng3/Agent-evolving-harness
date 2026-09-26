import json, sys, collections
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, act_of, ORDER
from cvict_layers import events
R="/net/scratch/ymeng3/bos_alfworld"; idx=json.load(open(f"{R}/probeL/noop_index.json")); res=collections.defaultdict(lambda:[0,0,0])
for k in range(5):
    f=f"{R}/results/NOOP_{k}_seed1.json"
    try: d=json.load(open(f))
    except Exception: print(f"group {k} missing"); continue
    ga=d.get("games_actual") or d["games"]; won={g:bool(w) for g,w in zip(ga,d["won"])}; calls=d["calls"]
    for t in idx:
        if t["group"]!=k or t["game"] not in won: continue
        res[t["kind"]][0]+=1; res[t["kind"]][1]+=int(not won[t["game"]])   # outcome LOST after no-op
    print(f"group {k}: {len(ga)} episodes replayed, LLM calls {calls}")
for kind,(n,lost,_) in res.items(): print(f"  {kind:9s}: no-op of the step -> outcome lost in {lost}/{n} ({100*lost/max(n,1):.0f}%)")
c=res["credited"]; ctl=res["control"]; print(f"VICT-style check: credited-step no-op breaks the win {100*c[1]/max(c[0],1):.0f}% vs control {100*ctl[1]/max(ctl[0],1):.0f}%  (VICT ALFWorld: 55/60 credited)")
