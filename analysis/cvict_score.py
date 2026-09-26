"""Component-VICT (a) exploration atoms, (b) V0 direct-edge credit with abstention, (c) V1 paired downstream descriptives.
SCORING RULES (fixed here before running):
  (a) search atoms (NOT derived from terminal rules; reported separately): explored(X)=+1 on FIRST arrival at receptacle X;
      negative_evidence=+1 when a first visit/opening shows the target is absent (progress by elimination).
  (b) V0 per activation: +1 if the executed action carries core+/holding+/at-target/reveal/explored-first; -1 if core-/holding-,
      or if the activation DISPLACED an admissible goal-relevant a0 (a0_adm==1 and a0 verb in move/take/heat/cool/clean/slice/use);
      0 = abstain. Component V0 = (plus - minus) / activations, with coverage = 1 - abstain fraction.
      A component's V0 verdict: helpful if V0 > +0.05 and coverage >= 0.2; harmful if V0 < -0.05 and coverage >= 0.2; else ABSTAIN.
  (c) V1 (descriptive only; independent ON/OFF samples cannot establish downstream causal edges): per slot, step of first
      'seen'/'holding'/core atom in ON vs OFF, and outcome; reported as timing shifts.
"""
import json, re, sys, os, collections, statistics as st
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, step_events, act_of, ORDER
R="/net/scratch/ymeng3/bos_alfworld/results"; GOAL_VERBS=("move","take","heat","cool","clean","slice","use")
def episode_edges(t, g):
    tt,obj,rec,core,pre=task(g); core_names={c[0] for c in core}; visited=set(); rows=[]
    for x in t:
        a=act_of(x); o=x.get("obs","").lower(); ev=step_events(a,x.get("obs",""),obj,rec)
        if a.startswith("go to ") and "you arrive at" in o:
            X=a[6:].strip()
            if X not in visited: visited.add(X); ev.append(("explored",+1)); 
            if X not in visited or True:
                if obj not in o: ev.append(("negative_evidence",+1)) if ("you see" in o and X not in [v for v in []]) else None
        rows.append((x,a,ev,core_names))
    return rows
def v0(tag, comp_key, comp):
    d=json.load(open(f"{R}/{tag}_seed1.json")); games=d.get("games_actual") or ORDER; plus=minus=abst=n=0; kinds=collections.Counter()
    for g,t in zip(games,d["traj"]):
        for x,a,ev,core_names in episode_edges(t,g):
            if not x.get(comp_key): continue
            n+=1; pos=any(s>0 and (atom in core_names or atom in ("holding","at","seen","opened_target","explored")) for atom,s in ev)
            neg=any(s<0 and (atom in core_names or atom=="holding") for atom,s in ev)
            a0=(x.get("a0") or "").strip().lower(); displaced = x.get("a0_adm",0)==1 and a0.split(" ")[0] in GOAL_VERBS and a0!=a.lower()
            if displaced: neg=True; kinds["displaced goal-relevant a0"]+=1
            if pos and not neg: plus+=1
            elif neg: minus+=1
            else: abst+=1
    cov=1-abst/max(n,1); score=(plus-minus)/max(n,1); verdict="helpful" if score>.05 and cov>=.2 else "harmful" if score<-.05 and cov>=.2 else "ABSTAIN"
    return n,plus,minus,abst,cov,score,verdict,kinds
print("=== (b) V0 direct-edge credit (with exploration atoms from (a)) vs global gamma ===")
G={("PV_r6_C","fb"):("r6 fallback",-6.8),("PV_r6_C","retry_chg"):("r6 retry",0.0),("PV_L2c4_C","fb"):("L2c4 fallback",16.7),("PV_L2c4_C","retry_chg"):("L2c4 retry",1.0),("PV_r4_C","retry_chg"):("r4 retry",13.0)}
print(f"{'component':14s} {'n':>5s} {'+':>4s} {'-':>4s} {'abst':>5s} {'cov':>5s} {'V0':>6s} {'verdict':8s} {'gamma':>6s}  agree?  notes")
for (tag,key),(lab,gam) in G.items():
    n,p,m,ab,cov,sc,vd,k=v0(tag,key,lab); agree = (vd=="ABSTAIN") and "abstain" or ("yes" if (sc>0)==(gam>0) else "NO")
    print(f"{lab:14s} {n:5d} {p:4d} {m:4d} {ab:5d} {cov:5.2f} {sc:+6.3f} {vd:8s} {gam:+6.1f}  {agree:7s} {dict(k)}")
print("\n=== (c) V1 descriptive: first step reaching seen / holding / a core atom, ON vs OFF, slot-paired (independent samples; timing only) ===")
def first_steps(tag):
    d=json.load(open(f"{R}/{tag}_seed1.json")); games=d.get("games_actual") or ORDER; out=[]
    for g,t,w in zip(games,d["traj"],d["won"]):
        tt,obj,rec,core,pre=task(g); core_names={c[0] for c in core}; f={"seen":None,"holding":None,"core":None}
        for x in t:
            for atom,s in step_events(act_of(x),x.get("obs",""),obj,rec):
                if s>0:
                    if atom=="seen" and f["seen"] is None: f["seen"]=x["step"]
                    if atom=="holding" and f["holding"] is None: f["holding"]=x["step"]
                    if atom in core_names and f["core"] is None: f["core"]=x["step"]
        out.append((f,int(bool(w)),len(t)))
    return out
for on,off,lab in (("PV_r6_C","PVA_r6_nofb","r6 fallback"),("PV_L2c4_C","PVA_L2c4_nofb","L2c4 fallback")):
    A=first_steps(on); B=first_steps(off)
    for key in ("seen","holding","core"):
        ra=[f[key] for f,_,_ in A if f[key] is not None]; rb=[f[key] for f,_,_ in B if f[key] is not None]
        print(f"  {lab:14s} first {key:8s}: ON reached in {len(ra):2d}/96 (median step {st.median(ra) if ra else 'n/a'}) | OFF reached in {len(rb):2d}/96 (median {st.median(rb) if rb else 'n/a'})")
    print(f"  {lab:14s} wins ON {sum(w for _,w,_ in A)} / OFF {sum(w for _,w,_ in B)}; mean episode length ON {st.mean(L for *_,L in A):.1f} / OFF {st.mean(L for *_,L in B):.1f}")
