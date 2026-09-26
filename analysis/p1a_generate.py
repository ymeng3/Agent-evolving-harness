import sys, os, json, re, copy, time
os.environ.setdefault("BOS_STATE", "/tmp/claude-21786/-home-ymeng3/a9602186-0f3f-4211-b98e-3fb5a5ae7fef/scratchpad/eqv/x.json")
sys.argv=["x"]; sys.path.insert(0,"/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag")
import closedloop as C
R="/net/scratch/ymeng3/bos_alfworld"; OUT="/net/scratch/ymeng3/bos_screens/hag/p1a"
OP = ("TRANSFORMATION: COMPOSE-COHERENT. Propose the intervention the evidence calls for. It MAY consist of several executable "
      "units (hooks/constants) ONLY when those units implement one coherent mechanism or address failure modes that interact; "
      "in that case add a line RATIONALE: stating how each unit depends on or interacts with the others. Do NOT bundle "
      "unrelated edits. There is no minimum or maximum number of units; a single-unit patch is correct when the evidence calls for one.")
C.MENU_ONE["ComposeCoherent"] = OP
def snapshot(arm, t):
    S=json.load(open(f"{R}/closedloop_state_{arm}.json")); A=S["arms"][arm]
    A["history"]=[x for x in A["history"] if x["round"]<t]; A["memory"]=[m for m in A["memory"] if m["round"]<t]
    A["archive"]=[a for a in A["archive"] if int(re.search(r"_r(\d+)_",a["name"]).group(1))<t]
    if arm=="naive": F = {"src":"","name":"F0","sha":C.sha("")} if t<=2 else A["F"]
    else: F = {"src":"","name":"F0","sha":C.sha("")} if t<=5 else A["F"]
    A["F"]=F; return S
STATES=[("naive",1),("naive",3),("naive",5),("ours",2),("ours",4),("ours",6)]
res=[]
for arm,t in STATES:
    S=snapshot(arm,t); F=S["arms"][arm]["F"]; Fres=S["cache"][F["sha"]]
    if F["src"]: open(f"{C.PATCH_DIR}/{F['name']}.py","w").write(F["src"]+"\n")
    names=[]
    for i in range(1,5):
        user=C.build_prompt(arm,S,Fres,"ComposeCoherent",i,json.dumps(names))
        resp=C.gpt4o([{"role":"system","content":C.SYS},{"role":"user","content":user}])
        m=re.search(r"```(?:python)?\s*(.*?)```",resp,re.S); src=m.group(1).strip() if m else ""
        nm=re.search(r"NAME:\s*([A-Za-z0-9_\-]+)",resp); rat=re.search(r"RATIONALE:\s*([^\n]+)",resp)
        vp=C.validate_patch(src)[0] if src else False; st=C.STATIC(src) if vp else False; sm=C.smoke(src,"x")["smoke_verdict"] if st else "SKIP"
        valid= bool(src) and vp and st and sm=="PASS"; U=list(C.units(src)[0]) if src else []
        rec={"state":f"{arm}@r{t}","i":i,"name":nm.group(1) if nm else "","valid":valid,"vp":vp,"static":st,"smoke":sm,"units":U,"m":len(U),
             "rationale":rat.group(1).strip() if rat else "","src":src,"resp":resp}
        names.append(rec["name"] or f"c{i}"); res.append(rec)
        print(f"{arm}@r{t} #{i} {rec['name'][:28]:28s} valid={valid} m={len(U)} units={U} rationale={'Y' if rat else 'N'}", flush=True)
        open(f"{OUT}/{arm}_r{t}_c{i}.json","w").write(json.dumps(rec,indent=1))
json.dump(res,open(f"{OUT}/all.json","w"),indent=1); print("spent", round(C.GUARD.spent(),3))
