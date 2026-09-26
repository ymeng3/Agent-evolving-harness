import json, random, statistics as st, glob, os, re
R="/net/scratch/ymeng3/bos_alfworld/results"; rng=random.Random(2026); out=[]
def W(tag,s=1):
    d=json.load(open(f"{R}/{tag}_seed{s}.json")); return [1 if w else 0 for w in d["won"]], d
def dec(a,b,B=4000):
    d=[x-y for x,y in zip(a,b)]; n=len(d); m=100*sum(d)/n; bs=sorted(100*sum(d[rng.randrange(n)] for _ in range(n))/n for _ in range(B))
    pk=sum(x>3 for x in bs)/B; pd=sum(x<-3 for x in bs)/B; return f"{m:+6.2f} [{bs[int(.025*B)]:+6.2f},{bs[int(.975*B)]:+6.2f}] {'KEEP' if pk>=.9 else 'DROP' if pd>=.9 else 'UNC'}"
out.append("=== r6 MECHANISM VARIANTS (96 games seed 1, paired by slot) ===")
C,_=W("P1B_ours_r6_strategic_fallback_with__C"); A,_=W("P1B_ours_r6_strategic_fallback_with__loo_choose"); M,_=W("P1B_ours_r6_strategic_fallback_with__loo_memory")
out.append(f"  C (ON/ON) {100*st.mean(C):.1f}% | C\\fallback {100*st.mean(A):.1f}% | C\\memory (look-only fb) {100*st.mean(M):.1f}%")
for tag,lab in (("R6V1_oneshot","V1 one-shot fallback"),("R6V2_histonly","V2 history-only fallback"),("R6V3_nofb_nomem","V3 no fallback, no memory")):
    try: V,d=W(tag)
    except Exception as e: out.append(f"  {lab}: MISSING ({e})"); continue
    fb=sum(x.get("fb",0) for t in d["traj"] for x in t)
    out.append(f"  {lab:28s} {100*st.mean(V):5.1f}%  api_err {d['api_errors']}  fb-flag steps {fb}  | vs C {dec(V,C)} | vs C\\fallback {dec(V,A)}")
out.append("  H_r6 predictions: V1-C\\fb in [-3,+3]; V2 <= C\\fb; V3-C\\fb in [-3,+3]; KILL if V1 <= C+2.")
out.append("\n=== A4 REPLAY EQUIVALENCE (full logged action sequences replayed under C, zero LLM calls) ===")
try:
    exp=json.load(open("/net/scratch/ymeng3/bos_alfworld/probeL/replaytest_expected.json"))["by_game"]; d=json.load(open(f"{R}/REPLAYTEST_r6_seed1.json"))
    ga=d.get("games_actual") or d["games"]; ok=0
    for g,t,w in zip(ga,d["traj"],d["won"]):
        e=exp.get(g); 
        if not e: out.append(f"  slot game not in expected set: {g[-50:]}"); continue
        n=min(len(e["obs"]),len(t)); same=sum(1 for i in range(n) if e["obs"][i]==t[i].get("obs","")); ok+=(same==n and bool(w)==bool(e["won"]))
        out.append(f"  {g.split('/')[-3][:38]:38s} obs identical {same}/{n}  outcome logged={e['won']} replayed={w}  LLM calls {d['calls'] if False else sum(x.get('calls',0) for x in t)}")
    out.append(f"  PASS games {ok}/8 (rule: 8/8) ; total LLM calls in the run: {d['calls']}")
except Exception as e: out.append(f"  replay test missing/failed: {e}")
out.append("\n=== PROBE L v2 (replay keyed by actual gamefile; fidelity checked) ===")
src={"r6fb":"PV_r6_C","l2fb":"PV_L2c4_C","r4rt":"PV_r4_C","r4hi":"PV_r4_C"}; glob_g={"r6fb":-6.8,"l2fb":16.7,"r4rt":13.0,"r4hi":-0.5}; locs={}
order=json.load(open("/net/scratch/ymeng3/bos_screens/hag/game_order_train96_seed1.json"))["games_actual"]
for s in ("r6fb","l2fb","r4rt","r4hi"):
    sd=json.load(open(f"{R}/{src[s]}_seed1.json")); lab2=dict(zip(order,sd["traj"])); rep=json.load(open(f"/net/scratch/ymeng3/bos_alfworld/probeL/{s}_replay.json"))
    on={};off={};fid=[0,0]
    for r in (1,2):
        for br,store in (("ON",on),("OFF",off)):
            f=f"{R}/PL_{s}_{br}_rep{r}_seed1.json"
            if not os.path.exists(f): continue
            d=json.load(open(f)); ga=d.get("games_actual") or d["games"]
            for g,w,t in zip(ga,d["won"],d["traj"]):
                store.setdefault(g,[]).append(1 if w else 0); n=len(rep.get(g,[])); e=[x.get("obs","") for x in lab2.get(g,[])[:n]]; got=[x.get("obs","") for x in t[:n]]
                fid[0]+=(e==got); fid[1]+=1
    games=sorted(set(on)&set(off)); diffs=[st.mean(on[g])-st.mean(off[g]) for g in games]
    if diffs:
        m=100*st.mean(diffs); se=100*st.pstdev(diffs)/len(diffs)**.5; locs[s]=m
        out.append(f"  {s}: states {len(games)} replay fidelity {fid[0]}/{fid[1]}  gamma_local {m:+6.1f} (SE {se:4.1f})  P(on) {100*st.mean(st.mean(on[g]) for g in games):.0f}% P(off) {100*st.mean(st.mean(off[g]) for g in games):.0f}%  | gamma_global {glob_g[s]:+.1f}")
    else: out.append(f"  {s}: MISSING")
if len(locs)==4:
    def rank(d):
        it=sorted(d,key=lambda k:-d[k]); return {k:i+1 for i,k in enumerate(it)}
    rl,rg=rank(locs),rank(glob_g); rho=1-6*sum((rl[k]-rg[k])**2 for k in locs)/(4*15)
    out.append(f"  Spearman(local, global) = {rho:.2f} (prediction > 0.7); sign agreement {sum(1 for k in locs if (locs[k]>0)==(glob_g[k]>0))}/4")
txt="\n".join(out); print(txt); open("/net/scratch/ymeng3/bos_screens/hag/overnight2_result.txt","w").write(txt+"\n")
