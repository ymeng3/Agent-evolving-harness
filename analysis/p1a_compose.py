import sys, os, json, re, glob
os.environ.setdefault("BOS_STATE", "/tmp/claude-21786/-home-ymeng3/a9602186-0f3f-4211-b98e-3fb5a5ae7fef/scratchpad/eqv/x.json")
sys.argv=["x"]; sys.path.insert(0,"/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag")
import closedloop as C, b2_prompts as BP, phasec_prompts as PC
R="/net/scratch/ymeng3/bos_alfworld"; OUT="/net/scratch/ymeng3/bos_screens/hag/p1a_compose"; os.makedirs(OUT, exist_ok=True)
OP=("TRANSFORMATION: COMPOSE. Select at least two source mechanisms from the MECHANISM POOL (or one pool mechanism plus one mechanism you derive "
    "from a specific failure in the evidence) that have a reason to interact or complement each other, and implement their composition as one patch. "
    "Each constituent must remain an identifiable executable unit (a hook or constant). Do not add edits that are not part of the composition.")
ART=("Output format, exactly:\nDESIGN_INTENT: <one sentence>\nSOURCE_A: <pool entry name, or 'derived'>\nEVIDENCE_A: <which evidence lines>\n"
     "SOURCE_B: <pool entry name, or 'derived'>\nEVIDENCE_B: <which evidence lines>\nSOURCE_C: <optional>\nEVIDENCE_C: <optional>\n"
     "COMPOSITION_HYPOTHESIS: <why these constituents interact or complement each other; name the shared state or control flow>\n"
     "MECHANISM: <the hooks/constants you change and how>\nNAME: <short_snake_case>\n```python\n<patch module>\n```")
def snapshot(arm,t):
    S=json.load(open(f"{R}/closedloop_state_{arm}.json")); A=S["arms"][arm]
    A["history"]=[x for x in A["history"] if x["round"]<t]; A["memory"]=[m for m in A["memory"] if m["round"]<t]
    A["archive"]=[a for a in A["archive"] if int(re.search(r"_r(\d+)_",a["name"]).group(1))<t]
    A["F"]={"src":"","name":"F0","sha":C.sha("")} if (t<=2 if arm=="naive" else t<=5) else A["F"]; return S
def pool(arm,t,S):
    L="N" if arm=="naive" else "O"; ents=[]
    for r in range(1,t):
        for k in (1,2,3,4):
            p=f"{C.PATCH_DIR}/CL_{'N' if r==1 else L}_r{r}_c{k}.py"
            if not os.path.exists(p): continue
            src=open(p).read().strip(); name=os.path.basename(p)[:-3]
            h=[x for x in S["arms"][arm]["history"] if x["name"].startswith(name)]
            ev=(f"finalist, validation delta vs parent {h[0]['delta']:+.2f} pp, {h[0]['decision']}" if h else "validated on 9-27 games, eliminated by the stopping rule (no full estimate)")
            g=[m for m in S["arms"][arm]["memory"] if m["round"]==r]
            if h and g: ev+="; Credit: "+", ".join(f"{m['unit']} gamma {m['gamma']:+.1f} ({m['decision']})" for m in g)
            ents.append((name,ev,src))
    return ents
STATES=[("naive",1),("naive",3),("naive",5),("ours",2),("ours",4),("ours",6)]; res=[]
for arm,t in STATES:
    S=snapshot(arm,t); F=S["arms"][arm]["F"]; Fres=S["cache"][F["sha"]]; fail,comp,mem=C.evidence_blocks(arm,S,Fres)
    P=pool(arm,t,S)
    pooltxt="MECHANISM POOL (candidates this lineage has validated so far; compose from these or derive one from the evidence):\n"+("".join(f"  [{n}] {e}\n```python\n{s}\n```\n" for n,e,s in P) if P else "  (empty at this round: derive both constituents from distinct failures in the evidence)\n")
    arch="ARCHIVE.\nThe archive's current entry, which your proposal descends from:\n\n```python\n"+(F["src"] or "# released harness: no patch")+"\n```\n"
    names=[]
    for i in range(1,5):
        user=f"[proposal attempt {i}]\n"+BP.header()+"\n"+arch+"\n"+fail+("\n"+mem if mem else "")+"\n"+pooltxt+"\n"+OP+"\n"+ART+"\n"+PC.FOOT.replace("{names}",json.dumps(names))+PC.DESC_TASK
        resp=C.gpt4o([{"role":"system","content":C.SYS},{"role":"user","content":user}])
        m=re.search(r"```(?:python)?\s*(.*?)```",resp,re.S); src=m.group(1).strip() if m else ""
        f=lambda k: (re.search(k+r":\s*([^\n]+)",resp) or [None,""])[1].strip() if re.search(k+r":\s*([^\n]+)",resp) else ""
        vp=C.validate_patch(src)[0] if src else False; st=C.STATIC(src) if vp else False; sm=C.smoke(src,"x")["smoke_verdict"] if st else "SKIP"
        valid=bool(src) and vp and st and sm=="PASS"; U=list(C.units(src)[0]) if src else []
        rec={"state":f"{arm}@r{t}","i":i,"pool_size":len(P),"name":f("NAME"),"valid":valid,"vp":vp,"static":st,"smoke":sm,"units":U,"m":len(U),
             "SOURCE_A":f("SOURCE_A"),"SOURCE_B":f("SOURCE_B"),"SOURCE_C":f("SOURCE_C"),"HYP":f("COMPOSITION_HYPOTHESIS"),"src":src,"resp":resp}
        names.append(rec["name"] or f"c{i}"); res.append(rec)
        print(f"{arm}@r{t} pool={len(P)} #{i} {rec['name'][:26]:26s} valid={valid} m={len(U)} A={rec['SOURCE_A'][:18]!r} B={rec['SOURCE_B'][:18]!r} units={U}", flush=True)
        json.dump(rec,open(f"{OUT}/{arm}_r{t}_c{i}.json","w"),indent=1)
json.dump(res,open(f"{OUT}/all.json","w"),indent=1)
