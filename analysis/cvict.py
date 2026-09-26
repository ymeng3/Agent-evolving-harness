"""Component-VICT feasibility (offline). Verifier trace with core + precondition atoms from observation text; reconstruction
check vs env 'won'; component -> action direct edges (fallback/retry) -> atoms; per-family coverage; audited examples.
Usage: cvict.py TAG [TAG...]   (step-logged passes; games resolved via games_actual or the recovered seed-1 order)"""
import json, re, sys, os, collections
R="/net/scratch/ymeng3/bos_alfworld/results"; ORDER=json.load(open("/net/scratch/ymeng3/bos_screens/hag/game_order_train96_seed1.json"))["games_actual"]
def task(game):
    t=json.load(open(os.path.join(os.path.dirname(game),"traj_data.json"))); p=t["pddl_params"]; tt=t["task_type"]
    obj=p["object_target"].lower(); rec=p["parent_target"].lower(); mrec=(p.get("mrecep_target") or "").lower(); tog=(p.get("toggle_target") or "").lower()
    core=[]; pre=[]
    if tt=="pick_two_obj_and_place": core=[("placed",obj,rec,2)]
    elif tt=="pick_and_place_with_movable_recep": core=[("in_mrecep",obj,mrec,1),("placed",mrec,rec,1)]
    elif tt=="look_at_obj_in_light": core=[("holding",obj,"",1),("toggled",tog,"",1)]
    else: core=[("placed",obj,rec,1)]
    if tt.startswith("pick_heat"): core.append(("heated",obj,"",1))
    if tt.startswith("pick_cool"): core.append(("cooled",obj,"",1))
    if tt.startswith("pick_clean"): core.append(("cleaned",obj,"",1))
    if p.get("object_sliced"): core.append(("sliced",obj,"",1))
    pre=[("holding",obj,"",1),("at",rec,"",1)]
    return tt,obj,rec,core,pre
VERB={"heat":"heated","cool":"cooled","clean":"cleaned","slice":"sliced"}
def step_events(a, o, obj, rec, mrec=""):
    """Return list of (atom, +1/-1) witnessed by executing action a with observation o."""
    a=a.lower().strip(); o=o.lower(); ev=[]
    if a.startswith("move ") and "you move" in o:
        m=re.match(r"move (.+?) \d* ?to (.+?) \d*$", a) or re.match(r"move (.+?) to (.+)$", a)
        if m:
            what=re.sub(r"\s*\d+$","",m.group(1)).strip(); where=re.sub(r"\s*\d+$","",m.group(2)).strip()
            if obj in what: ev.append(("holding",-1))
            if obj in what and rec in where: ev.append(("placed",+1))
            if mrec and obj in what and mrec in where: ev.append(("in_mrecep",+1))
            if mrec and mrec in what and rec in where: ev.append(("placed_m",+1))
    if a.startswith("take ") and "you pick up" in o:
        m=re.match(r"take (.+?) \d* ?from (.+)$", a)
        if m:
            what=re.sub(r"\s*\d+$","",m.group(1)).strip(); frm=re.sub(r"\s*\d+$","",m.group(2)).strip()
            if obj in what: ev.append(("holding",+1))
            if obj in what and rec in frm: ev.append(("placed",-1))
    for v,atom in VERB.items():
        if a.startswith(v+" ") and obj in a and f"you {v}" in o: ev.append((atom,+1))
    if a.startswith("use ") and "you turn on" in o: ev.append(("toggled",+1))
    if a.startswith("go to ") and "you arrive at" in o:
        where=re.sub(r"\s*\d+$","",a[6:]).strip()
        if rec in where: ev.append(("at",+1))
    # REVEAL witnesses (VICT 'evidence reveal'): the observation after this action shows the target object / opens the target receptacle
    if re.search(r"\b"+re.escape(obj)+r" \d", o) and ("you see" in o or "you open" in o or "you arrive" in o): ev.append(("seen",+1))
    if a.startswith("open ") and rec in a and "you open" in o: ev.append(("opened_target",+1))
    return ev
def act_of(x):
    m=re.search(r"<action>(.*?)</action>",x["action"]); return (m.group(1) if m else x["action"]).strip()
def run(tag):
    d=json.load(open(f"{R}/{tag}_seed1.json")); games=d.get("games_actual") or ORDER
    recon=[0,0]; fam=collections.defaultdict(lambda: [0,0,0,0]); kinds=collections.defaultdict(collections.Counter)  # activations, direct core/pre +, direct -, none
    examples=[]
    for gi,(g,t,w) in enumerate(zip(games,d["traj"],d["won"])):
        tt,obj,rec,core,pre=task(g); tdat=json.load(open(os.path.join(os.path.dirname(g),"traj_data.json"))); mrec=(tdat["pddl_params"].get("mrecep_target") or "").lower()
        cnt=collections.Counter(); core_names={c[0] for c in core}
        for x in t:
            a=act_of(x); ev=step_events(a,x.get("obs",""),obj,rec,mrec)
            for atom,s in ev: cnt[atom]+=s
            comps=[]
            if x.get("fb"): comps.append("fallback")
            if x.get("retry_chg"): comps.append("retry")
            if x.get("parse_chg"): comps.append("parse")
            for c in comps:
                fam[c][0]+=1; hit=[(atom,s) for atom,s in ev if atom in core_names or atom in ("holding","at","seen","opened_target")]
                kinds[c]["core+" if any(s>0 and atom in core_names for atom,s in hit) else "core-" if any(s<0 and atom in core_names for atom,s in hit) else "holding+" if any(atom=="holding" and s>0 for atom,s in hit) else "holding-" if any(atom=="holding" and s<0 for atom,s in hit) else "at-target" if any(atom=="at" for atom,_ in hit) else "reveal(seen/opened)" if any(atom in ("seen","opened_target") for atom,_ in hit) else "no-edge"]+=1
                if x.get("a0_adm",1)==0 and not x.get("a0","").strip().split(" ")[0] in ("go","open","take","move","put","heat","cool","clean","slice","use","look","examine","close","inventory"): kinds[c]["(a0 was not an action)"]+=1
                if any(s>0 for _,s in hit): fam[c][1]+=1
                elif any(s<0 for _,s in hit): fam[c][2]+=1
                else: fam[c][3]+=1
                if hit and any(atom!="at" for atom,_ in hit) and len(examples)<12: examples.append(f"    {tag} ep{gi} step{x['step']:2d} {c:8s} a0={x.get('a0','')[:28]!r} -> exec={a[:34]!r} obs={x.get('obs','')[:40]!r} edges={hit}")
        # reconstruction: all core atoms satisfied at the end?
        ok=all(cnt.get(c[0],0)>=c[3] for c in core); recon[0]+=(ok==bool(w)); recon[1]+=1
    print(f"\n{tag}: success {100*d['success_rate']:.1f}% | RECONSTRUCTION: atom-state predicts env 'won' in {recon[0]}/{recon[1]} episodes ({100*recon[0]/recon[1]:.0f}%)")
    for c,(n,p,m,z) in fam.items():
        k=kinds[c]; print(f"  {c:9s} activations {n:5d} | core+ {k['core+']:3d} core- {k['core-']:3d} holding+ {k['holding+']:3d} holding- {k['holding-']:3d} at-target {k['at-target']:3d} reveal {k['reveal(seen/opened)']:4d} no-edge {k['no-edge']:5d} -> direct-edge coverage {100*(n-k['no-edge'])/max(n,1):.1f}% | first parse was not an action in {k['(a0 was not an action)']} activations")
    print("  audited examples:"); print("\n".join(examples[:8]) if examples else "    (none)")
for tag in sys.argv[1:]: run(tag)
