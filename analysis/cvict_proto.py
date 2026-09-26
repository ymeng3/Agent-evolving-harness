import json, re, sys, collections
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, act_of, ORDER
from cvict_layers import events, load
def tagline(x, obj, rec, visited):
    a=act_of(x); core,expl=events(a,x.get("obs",""),obj,rec); tags=[f"{k}{'+' if s>0 else '-'}" for k,s in core]
    for e in expl:
        if e=="target_seen": tags.append("SEEN")
        elif e=="target_recep_opened": tags.append("OPENED-target")
        elif e.startswith("visit:"):
            if e[6:] not in visited: visited.add(e[6:]); tags.append("first-visit")
    flag=("FB" if x.get("fb") else "RT" if x.get("retry_chg") else "  ")
    a0=(x.get("a0") or "").strip().replace("\n"," ")[:22]
    return f"{x['step']:2d} {flag} exec={a[:30]:30s} a0={a0!r:26s} {'ADM' if x['admissible'] else 'inadm'} {' '.join(tags)}"
def window(t, obj, rec, s, k=6):
    visited=set(); out=[]
    for x in t:
        line=tagline(x,obj,rec,visited)
        if s-1<=x["step"]<=s+k: out.append("        "+line)
    return out
def coverage(tag,key,k=5):
    d,games=load(tag); n=direct=down=expl=0
    for g,t in zip(games,d["traj"]):
        tt,obj,rec,core,pre=task(g); core_names={c[0] for c in core}|{"holding","at"}; visited=set()
        evs=[events(act_of(x),x.get("obs",""),obj,rec) for x in t]
        for i,x in enumerate(t):
            for e in evs[i][1]:
                if e.startswith("visit:"): pass
            if not x.get(key): continue
            n+=1; c0=[e for e in evs[i][0] if e[0] in core_names]
            if c0: direct+=1; continue
            ahead=[e for j in range(i+1,min(i+1+k,len(t))) for e in evs[j][0] if e[0] in core_names and e[1]>0] + [e for j in range(i+1,min(i+1+k,len(t))) for e in evs[j][1] if e=="target_seen"]
            if ahead: down+=1; continue
            ex=[e for e in evs[i][1] if e=="target_recep_opened" or e.startswith("visit:")]
            if ex: expl+=1
    return n,direct,down,expl
print("=== ROUGH COVERAGE of activations: direct core/precondition hit | +downstream (core/holding/SEEN within 5 steps) | +exploration (visit/open) ===")
for tag,key,lab in (("PV_r6_C","fb","r6 fallback"),("PV_L2c4_C","fb","L2c4 fallback"),("PV_r6_C","retry_chg","r6 retry"),("PV_r4_C","retry_chg","r4 retry")):
    n,dr,dw,ex=coverage(tag,key); print(f"  {lab:14s} n={n:5d}  direct {100*dr/n:4.1f}%  +downstream5 {100*(dr+dw)/n:4.1f}%  +exploration {100*(dr+dw+ex)/n:4.1f}%")
print("  memory / HISTORY: no step-logged pass on either side -> not examinable from existing logs.")
print("\n=== PAIRED ON/OFF TRAJECTORY WINDOWS (pair-supported cases: the activation is the first divergence). FB=fallback fired, RT=retry changed the action ===")
for on,off,lab in (("PV_r6_C","PVA_r6_nofb","r6 fallback (harmful, gamma -6.8)"),("PV_L2c4_C","PVA_L2c4_nofb","L2c4 fallback (beneficial, gamma +16.7)")):
    A,gA=load(on); B,gB=load(off); shown=collections.Counter()
    print(f"\n--- {lab} ---")
    for gi,(g,ta,tb) in enumerate(zip(gA,A["traj"],B["traj"])):
        tt,obj,rec,core,pre=task(g); acts_a=[act_of(x) for x in ta]; acts_b=[act_of(x) for x in tb]
        div=next((j for j in range(min(len(acts_a),len(acts_b))) if acts_a[j]!=acts_b[j]), None); firsts=[x["step"] for x in ta if x.get("fb")]
        if div is None or not firsts or firsts[0]!=div: continue
        pat=("ON win / OFF lose" if A["won"][gi] and not B["won"][gi] else "ON lose / OFF win" if B["won"][gi] and not A["won"][gi] else "same outcome")
        if shown[pat]>=1 or sum(shown.values())>=3: continue
        shown[pat]+=1; s=div
        print(f"  ep{gi} task={tt} target={obj}->{rec}  [{pat}]  ON len {len(ta)} won={A['won'][gi]} | OFF len {len(tb)} won={B['won'][gi]}")
        print("      ON  (component present):"); print("\n".join(window(ta,obj,rec,s)))
        print("      OFF (component removed):"); print("\n".join(window(tb,obj,rec,s)))
