"""Probe V: component -> action -> verifier atom tracing on step-logged passes. Atoms from task_type+pddl_params; witnesses
from the observation text after the action. Usage: python probeV_trace.py TAG [TAG...]"""
import json, os, re, sys
R="/net/scratch/ymeng3/bos_alfworld/results"
def atoms(game):
    t=json.load(open(os.path.join(os.path.dirname(game),"traj_data.json"))); p=t["pddl_params"]; tt=t["task_type"]
    obj=p["object_target"].lower(); rec=p["parent_target"].lower(); mrec=(p.get("mrecep_target") or "").lower()
    A={"place":(obj,rec)}
    if tt.startswith("pick_heat"): A["heat"]=obj
    if tt.startswith("pick_cool"): A["cool"]=obj
    if tt.startswith("pick_clean"): A["clean"]=obj
    if p.get("object_sliced"): A["slice"]=obj
    if tt.startswith("look_at_obj"): A["toggle"]=(p.get("toggle_target") or "").lower()
    if mrec: A["mplace"]=(obj,mrec)
    return tt, A
def witness(obs, act, A):
    """+1 establish, -1 destroy, 0 none, for the goal atoms. ALFWorld verbs: 'move X to Y' (put), 'take X from Y', 'heat/cool/clean X with Y'."""
    o=obs.lower(); a=act.lower(); obj,rec=A["place"]
    if a.startswith("move") and obj in a and rec in a and "you move" in o: return +1,"place"
    if a.startswith("take") and obj in a and rec in a and "you pick up" in o: return -1,"place"
    for k in ("heat","cool","clean"):
        if k in A and a.startswith(k) and A[k] in a and f"you {k}" in o: return +1,k
    if "slice" in A and a.startswith("slice") and A["slice"] in a and "you slice" in o: return +1,"slice"
    if "toggle" in A and a.startswith("use") and A["toggle"] in a and "you turn on" in o: return +1,"toggle"
    return 0,None
def profile(tag):
    d=json.load(open(f"{R}/{tag}_seed1.json")); d["games"]=d.get("games_actual") or json.load(open("/net/scratch/ymeng3/bos_screens/hag/game_order_train96_seed1.json"))["games_actual"]; P={"retry":[0,0,0,0],"fallback":[0,0,0,0],"parse":[0,0,0,0],"none":[0,0,0,0]}  # activations, +, -, 0
    trig=set()
    for g,t in zip(d["games"],d["traj"]):
        tt,A=atoms(g)
        for x in t:
            act=x["action"]; m=re.search(r"<action>(.*?)</action>",act); act=m.group(1) if m else act
            w,_=witness(x.get("obs",""),act,A)
            comps=[]
            if x.get("retry_chg"): comps.append("retry")
            if x.get("fb"): comps.append("fallback")
            if x.get("parse_chg"): comps.append("parse")
            if not comps: comps=["none"]
            for c in comps:
                P[c][0]+=1; P[c][1 if w>0 else 2 if w<0 else 3]+=1
    return d["success_rate"], P
for tag in sys.argv[1:]:
    sr,P=profile(tag); print(f"\n{tag}: success {100*sr:.1f}%")
    for c,(n,pl,mi,ze) in P.items(): print(f"  {c:9s} activations {n:5d}  +atom {pl:4d}  -atom {mi:4d}  none {ze:5d}   net/activation {((pl-mi)/n if n else 0):+.3f}")
