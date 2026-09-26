"""Probe L builder: from a step-logged C pass, pick the first activation state of a component in up to 8 games, write a
replay file {game: prefix_actions} + manifest, and a jobs file with ON (C) / OFF (C\\e) branches x 2 replicates.
Usage: build_probeL.py TAG COMP C_PATCH OFF_PATCH OUTNAME [B=8] [OFF_ONLY=0]   where COMP in fallback|retry|parse|history"""
import json, os, re, sys, random
R="/net/scratch/ymeng3/bos_alfworld"; tag, comp, cpatch, offpatch, out = sys.argv[1:6]; B=int(sys.argv[6]) if len(sys.argv)>6 else 8; OFF_ONLY=(len(sys.argv)>7 and sys.argv[7]=="1")
d=json.load(open(f"{R}/results/{tag}_seed1.json")); rng=random.Random(42); picks=[]
ACT=json.load(open("/net/scratch/ymeng3/bos_screens/hag/game_order_train96_seed1.json"))["games_actual"]; d["games"]=d.get("games_actual") or ACT   # key prefixes by ACTUAL gamefile
ORIG={}
for g,t,w in zip(d["games"], d["traj"], d["won"]):
    ORIG[g]=int(bool(w))
    tstar=None
    for x in t:
        if comp=="fallback" and x.get("fb"): tstar=x["step"]; break
        if comp=="retry" and x.get("retry_chg"): tstar=x["step"]; break
        if comp=="parse" and x.get("parse_chg"): tstar=x["step"]; break
        if comp=="history" and x["step"]>=6: tstar=6; break
    if tstar is None or tstar>=45: continue
    acts=[]
    for x in t[:tstar]:
        m=re.search(r"<action>(.*?)</action>", x["action"]); acts.append(m.group(1) if m else x["action"])
    picks.append((g, tstar, acts, len(t)))
rng.shuffle(picks); picks=picks[:B]
os.makedirs(f"{R}/probeL", exist_ok=True)
json.dump({g:acts for g,_,acts,_ in picks}, open(f"{R}/probeL/{out}_replay.json","w"), indent=0)
open(f"{R}/probeL/{out}_manifest.txt","w").write("".join(g+"\n" for g,_,_,_ in picks))
jobs=(f"PL_{out}_OFF_rep1 {offpatch} 1\n" if OFF_ONLY else "".join(f"PL_{out}_{br}_rep{r} {p} 1\n" for r in (1,2) for br,p in (("ON",cpatch),("OFF",offpatch))))
json.dump({g:{"won_on_original":ORIG[g],"tstar":t,"len":L} for g,t,acts,L in picks}, open(f"{R}/probeL/{out}_meta.json","w"))
open(f"{R}/probeL/{out}_jobs.txt","w").write(jobs)
print(f"{out}: {len(picks)} activation states | t* = {[t for _,t,_,_ in picks]} | episode lengths {[L for *_,L in picks]} | mean prefix fraction {sum(t/L for _,t,_,L in picks)/max(len(picks),1):.2f} | 4 jobs of {len(picks)} games")
