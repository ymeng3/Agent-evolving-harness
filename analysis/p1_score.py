"""Phase-1 read-out: CF@8 / CF@32 = mean(won_on_original - won_off) over the first B states (manifest order); cost = OFF-branch LLM calls vs the full C pass."""
import json, os, statistics as st
R="/net/scratch/ymeng3/bos_alfworld"; SETS=[("p1_r6fb","r6 fallback",-6.8,"PV_r6_C"),("p1_l2fb","L2c4 fallback",16.7,"PV_L2c4_C"),("p1_r4rt","r4 retry",13.0,"PV_r4_C"),("p1_r4hi","r4 HISTORY",-0.5,"PV_r4_C"),("p1_r6hi","r6 HISTORY",3.1,"PV_r6_C"),
  ("p1_m7fb","MECH07 fallback",-16.4,"XS_MECH07_C"),("p1_n5rt","naive r5 retry",13.5,"XS_naiver5_C"),("p1_c21rt","ctrl21 retry",8.2,"XS_ctrl21_C"),("p1_r3tp","r3 TEMPERATURE",-4.2,"XS_r3_C"),("p1_r3rt","r3 retry",None,"XS_r3_C")]
rows=[]; print(f"{'component':16s} {'global':>7s} {'CF@8':>7s} {'CF@32':>7s} {'n':>3s} {'P(on)':>6s} {'P(off)':>6s} {'OFF calls':>9s} {'C-pass calls':>12s} {'cost%':>6s}")
for s,lab,g,ctag in SETS:
    f=f"{R}/results/PL_{s}_OFF_rep1_seed1.json"; meta=f"{R}/probeL/{s}_meta.json"
    if not os.path.exists(f) or not os.path.exists(meta): print(f"{lab:16s} pending"); continue
    d=json.load(open(f)); M=json.load(open(meta)); order=[l.strip() for l in open(f"{R}/probeL/{s}_manifest.txt") if l.strip()]
    ga=d.get("games_actual") or d["games"]; off={g_:(1 if w else 0) for g_,w in zip(ga,d["won"])}; calls={g_:sum(x.get("calls",0) for x in t if not x.get("replayed")) for g_,t in zip(ga,d["traj"])}
    diffs=[M[g_]["won_on_original"]-off[g_] for g_ in order if g_ in off]; c8=100*st.mean(diffs[:8]); c32=100*st.mean(diffs)
    cpass=json.load(open(f"{R}/results/{ctag}_seed1.json"))["calls"]; offc=sum(calls[g_] for g_ in order if g_ in calls)
    pon=st.mean(M[g_]["won_on_original"] for g_ in order); poff=st.mean(off[g_] for g_ in order if g_ in off)
    rows.append((lab,g,c32)); print(f"{lab:16s} {(f'{g:+7.1f}' if g is not None else '    n/a'):>7s} {c8:+7.1f} {c32:+7.1f} {len(diffs):3d} {100*pon:6.0f} {100*poff:6.0f} {offc:9d} {cpass:12d} {100*offc/cpass:6.1f}")
known=[(l,g,c) for l,g,c in rows if g is not None]
if len(known)>=4:
    def rank(v): o=sorted(range(len(v)),key=lambda i:-v[i]); r=[0]*len(v); 
    import math
    gs=[g for _,g,_ in known]; cs=[c for _,_,c in known]; n=len(gs)
    rg=sorted(range(n),key=lambda i:-gs[i]); rc=sorted(range(n),key=lambda i:-cs[i]); pg=[0]*n; pc=[0]*n
    for k,i in enumerate(rg): pg[i]=k
    for k,i in enumerate(rc): pc[i]=k
    rho=1-6*sum((pg[i]-pc[i])**2 for i in range(n))/(n*(n*n-1)); print(f"Spearman(CF@32, global) over {n} components = {rho:.2f}")
    helpful=[c for l,g,c in known if l in ("L2c4 fallback","r4 retry","naive r5 retry","ctrl21 retry")]; harmful=[c for l,g,c in known if l in ("r6 fallback","MECH07 fallback")]
    if helpful and harmful: print(f"KILL CHECK: min(helpful CF@32)={min(helpful):+.1f} vs max(harmful CF@32)={max(harmful):+.1f} -> {'ORDERED (continue)' if min(helpful)>max(harmful) else 'NOT ORDERED (kill rule)'}")
