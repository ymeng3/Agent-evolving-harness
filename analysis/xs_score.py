"""Frozen exploration signal (EXPLORATION_SIGNAL_FROZEN.md). S for trigger components; T for every-step components."""
import json, re, sys, collections
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, act_of, ORDER
from cvict_layers import events
R="/net/scratch/ymeng3/bos_alfworld/results"
def load(tag): d=json.load(open(f"{R}/{tag}_seed1.json")); return d, (d.get("games_actual") or ORDER[:len(d["traj"])])
def S(tag,key,variant="A"):
    d,games=load(tag); labels=[]; kinds=collections.Counter()
    for g,t in zip(games,d["traj"]):
        tt,obj,rec,core,pre=task(g); core_names={c[0] for c in core}|{"holding","at"}; visited=set(); state=collections.Counter()
        for x in t:
            a=act_of(x); ev,expl=events(a,x.get("obs",""),obj,rec)
            visit=[e[6:] for e in expl if e.startswith("visit:")]; first=any(v not in visited for v in visit); revisit=bool(visit) and not first
            opened_first = variant=="B" and (a.startswith("open ") or a.startswith("examine ")) and a not in visited and ("you open" in x.get("obs","").lower() or "you see" in x.get("obs","").lower() or "on the" in x.get("obs","").lower())
            owns = bool(x.get(key)) and not (variant=="B" and key=="retry_chg" and x.get("fb"))
            posfact=[e for e in ev if e[1]>0 and e[0] in core_names]; redundant=any(state[e[0]]>=1 and e[0]!="at" for e in posfact)
            if owns:
                if a=="look": lab=-1; kinds["look"]+=1
                elif revisit: lab=-1; kinds["revisit"]+=1
                elif redundant: lab=-1; kinds["redundant"]+=1
                elif first or opened_first or "target_seen" in expl or posfact: lab=+1; kinds["first-visit" if first else "first-open" if opened_first else "seen/fact"]+=1
                else: lab=0; kinds["other"]+=1
                labels.append(lab)
            for v in visit: visited.add(v)
            if a.startswith("open ") or a.startswith("examine "): visited.add(a)
            for e in ev: state[e[0]]+=e[1]
    s=sum(labels)/max(len(labels),1); return len(labels), s, ("positive" if s>.05 else "negative" if s<-.05 else "undecided"), dict(kinds)
def T(on_tag, off_tag):
    def reach(tag):
        d,games=load(tag); seen=hold=core=0
        for g,t in zip(games,d["traj"]):
            tt,obj,rec,cr,pre=task(g); cn={c[0] for c in cr}; f={"s":0,"h":0,"c":0}
            for x in t:
                ev,expl=events(act_of(x),x.get("obs",""),obj,rec)
                if "target_seen" in expl: f["s"]=1
                for e,s_ in ev:
                    if s_>0 and e=="holding": f["h"]=1
                    if s_>0 and e in cn: f["c"]=1
            seen+=f["s"]; hold+=f["h"]; core+=f["c"]
        n=len(d["traj"]); return seen/n, hold/n, core/n, n
    a=reach(on_tag); b=reach(off_tag); t=(a[0]-b[0])+(a[1]-b[1])+(a[2]-b[2])
    return t, ("positive" if t>.05 else "negative" if t<-.05 else "undecided"), a, b
if __name__=="__main__":
    print("=== S on OLD logs (rule check, not a prediction) ===")
    for tag,key,lab,loo in (("PV_r6_C","fb","r6 fallback",-6.8),("PV_L2c4_C","fb","L2c4 fallback",16.7),("PV_r6_C","retry_chg","r6 retry",0.0),("PV_L2c4_C","retry_chg","L2c4 retry",1.0),("PV_r4_C","retry_chg","r4 retry",13.0)):
        n,s,v,k=S(tag,key); print(f"  {lab:14s} n={n:5d} S={s:+.3f} -> {v:9s} | LOO {loo:+.1f} | {k}")
    print("=== T on OLD paired logs ===")
    for on,off,lab,loo in (("PV_r6_C","PVA_r6_nofb","r6 fallback (as every-step check)",-6.8),("PV_L2c4_C","PVA_L2c4_nofb","L2c4 fallback",16.7)):
        t,v,a,b=T(on,off); print(f"  {lab:34s} T={t:+.3f} -> {v:9s} | LOO {loo:+.1f} | ON seen/hold/core {a[0]:.2f}/{a[1]:.2f}/{a[2]:.2f} OFF {b[0]:.2f}/{b[1]:.2f}/{b[2]:.2f}")
