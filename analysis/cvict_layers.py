"""Component-VICT layered offline experiment: (b) strict V0 -> (c) V1 path audit -> (a) exploration evidence. $0.
Rules fixed before running. Trusted LOO 3-class labels from CVICT_EVAL_TABLE (delta=2pp): r6 fallback harmful? (CI [-12.5,-1.6] ->
harmful at delta=2? UCB -1.6 > -2 -> neutral/unc under delta=2; harmful under delta=1). We report both delta=2 (frozen) and delta=1."""
import json, re, sys, collections, statistics as st
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, act_of, ORDER, VERB
R="/net/scratch/ymeng3/bos_alfworld/results"
LOO={"r6 fallback":(-6.77,-12.5,-1.6),"r6 retry":(0.0,-7.3,7.3),"L2c4 fallback":(16.67,1.0,32.3),"L2c4 retry":(1.04,-12.5,14.6),"r4 retry":(13.02,7.3,18.8)}
def cls(m,lo,hi,d): return "harmful" if hi<-d else "helpful" if lo>d else "neutral/unc"
def events(a,o,obj,rec):
    """core/precondition witnesses only (strict); plus separately-tagged exploration evidence."""
    a=a.lower().strip(); o=o.lower(); core=[]; expl=[]
    if a.startswith("move ") and "you move" in o:
        m=re.match(r"move (.+?) to (.+)$",a)
        if m:
            what=re.sub(r"\s*\d+$","",m.group(1)).strip(); where=re.sub(r"\s*\d+$","",m.group(2)).strip()
            if obj in what: core.append(("holding",-1))
            if obj in what and rec in where: core.append(("placed",+1))
    if a.startswith("take ") and "you pick up" in o:
        m=re.match(r"take (.+?) from (.+)$",a)
        if m:
            what=re.sub(r"\s*\d+$","",m.group(1)).strip(); frm=re.sub(r"\s*\d+$","",m.group(2)).strip()
            if obj in what: core.append(("holding",+1))
            if obj in what and rec in frm: core.append(("placed",-1))
    for v,atom in VERB.items():
        if a.startswith(v+" ") and obj in a and f"you {v}" in o: core.append((atom,+1))
    if a.startswith("use ") and "you turn on" in o: core.append(("toggled",+1))
    if a.startswith("go to ") and "you arrive at" in o:
        where=re.sub(r"\s*\d+$","",a[6:]).strip()
        if rec in where: core.append(("at",+1))
    if re.search(r"\b"+re.escape(obj)+r" \d",o) and ("you see" in o or "you open" in o or "you arrive" in o): expl.append("target_seen")
    if a.startswith("open ") and rec in a and "you open" in o: expl.append("target_recep_opened")
    if a.startswith("go to ") and "you arrive at" in o: expl.append("visit:"+a[6:].strip())
    return core,expl
def load(tag): d=json.load(open(f"{R}/{tag}_seed1.json")); return d, (d.get("games_actual") or ORDER)
def layer_b_a(tag,key,lab):
    d,games=load(tag); n=0; ep_act=0; ep_cov=set(); c=collections.Counter(); ex_c=collections.Counter(); redundant=0; sub_kind=collections.Counter()
    for gi,(g,t) in enumerate(zip(games,d["traj"])):
        tt,obj,rec,core,pre=task(g); core_names={x[0] for x in core}|{"holding","at"}; state=collections.Counter(); visited=set(); has=False
        for x in t:
            a=act_of(x); ev,expl=events(a,x.get("obs",""),obj,rec)
            if x.get(key):
                n+=1; has=True
                pos=[e for e in ev if e[1]>0 and e[0] in core_names]; neg=[e for e in ev if e[1]<0 and e[0] in core_names]
                red=[e for e in pos if state[e[0]]>=1 and e[0]!="at"]   # re-establishing an already-true atom (descriptive only)
                if red: redundant+=1
                if pos and not neg: c["+"]+=1; ep_cov.add(gi)
                elif neg: c["-"]+=1; ep_cov.add(gi)
                else: c["abstain"]+=1
                if key=="fb": sub_kind["look" if a=="look" else "repeat/other"]+=1
                # exploration evidence layer (a): counts only for abstained activations
                if not pos and not neg:
                    first_visit = any(e.startswith("visit:") and e[6:] not in visited for e in expl)
                    if "target_seen" in expl or "target_recep_opened" in expl: ex_c["reveal"]+=1
                    elif first_visit: ex_c["first_visit"]+=1
                    else: ex_c["none"]+=1
            for e in ev: state[e[0]]+=e[1]
            for e in expl:
                if e.startswith("visit:"): visited.add(e[6:])
        ep_act+=has
    N=len(d["traj"]); score=(c["+"]-c["-"])/max(n,1); cov=(c["+"]+c["-"])/max(n,1)
    vd="helpful" if score>.05 and cov>=.2 else "harmful" if score<-.05 and cov>=.2 else "ABSTAIN(cov<.2)" if cov<.2 else "ABSTAIN"
    m,lo,hi=LOO[lab]; l2=cls(m,lo,hi,2); l1=cls(m,lo,hi,1)
    agree=("n/a" if vd.startswith("ABSTAIN") or l2=="neutral/unc" else ("yes" if vd==l2 else "NO"))
    print(f"  {lab:14s} activations {n:5d} in {ep_act:2d}/{N} episodes | evidence-bearing {100*cov:4.1f}% of activations, {len(ep_cov):2d} episodes | + {c['+']:4d}  - {c['-']:3d}  abstain {c['abstain']:5d} | V0 {score:+.3f} -> {vd:16s} | LOO {m:+6.1f} [{lo:+.1f},{hi:+.1f}] class d2={l2:11s} d1={l1:11s} agree(d2)={agree}")
    print(f"      (a) exploration evidence on abstained activations: reveal {ex_c['reveal']}, first-visit {ex_c['first_visit']}, none {ex_c['none']} -> V0+expl coverage {100*(c['+']+c['-']+ex_c['reveal']+ex_c['first_visit'])/max(n,1):.1f}% (reported separately; NOT verifier atoms)")
    if key=="fb": print(f"      fallback substitution kinds: {dict(sub_kind)}; activations re-establishing an already-true atom (redundant): {redundant}")
    return redundant
print("=== (b) STRICT V0: component -> executed action -> existing core/precondition atom; abstain otherwise ===")
for tag,key,lab in (("PV_r6_C","fb","r6 fallback"),("PV_r6_C","retry_chg","r6 retry"),("PV_L2c4_C","fb","L2c4 fallback"),("PV_L2c4_C","retry_chg","L2c4 retry"),("PV_r4_C","retry_chg","r4 retry")):
    layer_b_a(tag,key,lab)
print("  other 30 pairs of the frozen table: NOT DETERMINABLE (no step logs).")
print("\n=== won-state-machine mismatch audit ===")
for tag in ("PV_r6_C","PV_L2c4_C","PV_r4_C","PVA_r6_nofb","PVA_L2c4_nofb"):
    d,games=load(tag)
    for gi,(g,t,w) in enumerate(zip(games,d["traj"],d["won"])):
        tt,obj,rec,core,pre=task(g); state=collections.Counter()
        for x in t:
            for e,s in events(act_of(x),x.get("obs",""),obj,rec)[0]: state[e]+=s
        ok=all(state.get(c[0],0)>=c[3] for c in core)
        if ok!=bool(w): print(f"  {tag} ep{gi} {tt} obj={obj} rec={rec} won={w} atoms={dict(state)} core={[(c[0],c[3]) for c in core]} last_actions={[act_of(x) for x in t[-3:]]}")
print("\n=== (c) V1 PATH AUDIT on paired ON/OFF logs (no scoring). Pair-supported downstream edge requires an IDENTICAL action prefix up to the activation step. ===")
for on,off,key,lab in (("PV_r6_C","PVA_r6_nofb","fb","r6 fallback"),("PV_L2c4_C","PVA_L2c4_nofb","fb","L2c4 fallback"),("PV_r6_C","PVA_r6_nofb","retry_chg","r6 retry (OFF still has retry: pair is C vs C\\fallback)")):
    A,gA=load(on); B,gB=load(off); assert gA==gB; kinds=collections.Counter(); samples=[]
    for gi,(g,ta,tb) in enumerate(zip(gA,A["traj"],B["traj"])):
        acts_a=[act_of(x) for x in ta]; acts_b=[act_of(x) for x in tb]
        div=next((j for j in range(min(len(acts_a),len(acts_b))) if acts_a[j]!=acts_b[j]), min(len(acts_a),len(acts_b)))
        firsts=[x["step"] for x in ta if x.get(key)]
        if not firsts: kinds["no activation"]+=1; continue
        s=firsts[0]
        if s<div: kinds["temporal-only (pair diverged before activation)"]+=0  # impossible ordering; placeholder
        if s==div: kinds["pair-supported: activation IS the first divergence"]+=1; samples.append((gi,s,acts_a[s],acts_b[s] if s<len(acts_b) else None,A["won"][gi],B["won"][gi]))
        elif s<div: kinds["pair-supported: identical prefix beyond activation (OFF chose same action)"]+=1
        else: kinds["temporal-only (pair diverged before activation)"]+=1
    print(f"  {lab}: {dict(kinds)}")
    for gi,s,aa,ab,wa,wb in samples[:6]: print(f"      ep{gi} step{s}: ON exec={aa!r} vs OFF exec={ab!r} -> outcome ON={wa} OFF={wb}")
