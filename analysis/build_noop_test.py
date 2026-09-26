"""VICT-style edge validation: replace one credited action with a no-op ('look'), replay everything else (env only, zero LLM),
and check whether the outcome/atom is lost. Credited = step whose action established a core atom (placed/heated/cooled/cleaned)
or 'holding' in a WON episode. Control = a random non-credited, non-final step of the same episode. Groups episodes into
manifests with distinct games. Output: probeL/noop_<k>_{replay,manifest}.json/txt + noop_index.json"""
import json, re, random, sys, os
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from cvict import task, act_of, ORDER
from cvict_layers import events
R="/net/scratch/ymeng3/bos_alfworld"; rng=random.Random(8); tests=[]
for tag in ("PV_r6_C","PV_L2c4_C","PV_r4_C"):
    d=json.load(open(f"{R}/results/{tag}_seed1.json")); games=d.get("games_actual") or ORDER
    for g,t,w in zip(games,d["traj"],d["won"]):
        if not w: continue
        tt,obj,rec,core,pre=task(g); acts=[act_of(x) for x in t]; cred=[]
        for i,x in enumerate(t):
            ev,_=events(acts[i],x.get("obs",""),obj,rec)
            if any(s>0 and k in ("placed","heated","cooled","cleaned","holding") for k,s in ev): cred.append(i)
        if not cred: continue
        ci=rng.choice(cred); noncred=[i for i in range(len(t)-1) if i not in cred and not acts[i].startswith("look")]
        if not noncred: continue
        ki=rng.choice(noncred)
        tests.append({"game":g,"tag":tag,"kind":"credited","step":ci,"orig":acts[ci],"actions":acts[:ci]+["look"]+acts[ci+1:]})
        tests.append({"game":g,"tag":tag,"kind":"control","step":ki,"orig":acts[ki],"actions":acts[:ki]+["look"]+acts[ki+1:]})
rng.shuffle(tests); tests=tests[:120]
# group into manifests with distinct games
groups=[]
for tt in tests:
    for grp in groups:
        if tt["game"] not in grp: grp[tt["game"]]=tt; break
    else: groups.append({tt["game"]:tt})
os.makedirs(f"{R}/probeL",exist_ok=True); index=[]
for k,grp in enumerate(groups):
    json.dump({g:v["actions"] for g,v in grp.items()},open(f"{R}/probeL/noop_{k}_replay.json","w"))
    open(f"{R}/probeL/noop_{k}_manifest.txt","w").write("".join(g+"\n" for g in grp))
    open(f"{R}/probeL/noop_{k}_jobs.txt","w").write(f"NOOP_{k} none 1\n")   # patch irrelevant in replay-only mode
    for g,v in grp.items(): index.append({**v,"group":k,"actions":None})
json.dump(index,open(f"{R}/probeL/noop_index.json","w"),indent=0)
print(f"{len(tests)} tests ({sum(1 for t in tests if t['kind']=='credited')} credited, {sum(1 for t in tests if t['kind']=='control')} control) in {len(groups)} manifests of sizes {[len(g) for g in groups]}")
