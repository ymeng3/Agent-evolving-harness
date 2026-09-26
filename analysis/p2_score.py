"""Phase-2 read-out: CF@B for B in 8/16/32/48 (nested), vs global point gamma; 3-class agreement (delta=3); by family."""
import json, os, statistics as st, sys
sys.path.insert(0,"/net/scratch/ymeng3/bos_screens/hag"); from p2_components import C
R="/net/scratch/ymeng3/bos_alfworld"; rows=[]
def cls(v,d=3): return "harmful" if v<-d else "helpful" if v>d else "neutral"
print(f"{'component':18s} {'kind':9s} {'global':>7s} {'CF@8':>6s} {'CF@16':>6s} {'CF@32':>6s} {'CF@48':>6s} {'n':>3s} {'cost%':>6s}")
for name,src,kind,cp,op,g in C:
    s="p2_"+name.replace(" ","_"); f=f"{R}/results/PL_{s}_OFF_rep1_seed1.json"; meta=f"{R}/probeL/{s}_meta.json"
    if not (os.path.exists(f) and os.path.exists(meta)): print(f"{name:18s} {kind:9s} pending/none"); continue
    d=json.load(open(f)); M=json.load(open(meta)); order=[l.strip() for l in open(f"{R}/probeL/{s}_manifest.txt") if l.strip()]
    ga=d.get("games_actual") or d["games"]; off={x:(1 if w else 0) for x,w in zip(ga,d["won"])}; calls=sum(sum(x.get("calls",0) for x in t if not x.get("replayed")) for t in d["traj"])
    diffs=[M[x]["won_on_original"]-off[x] for x in order if x in off]; n=len(diffs)
    cf={B:100*st.mean(diffs[:B]) for B in (8,16,32,48) if n>=min(B,8)}
    ctag=src; cpass=json.load(open(f"{R}/results/{ctag}_seed1.json"))["calls"]
    rows.append((name,kind,g,cf,n)); print(f"{name:18s} {kind:9s} {g:+7.1f} " + " ".join(f"{cf.get(B,float('nan')):+6.1f}" for B in (8,16,32,48)) + f" {n:3d} {100*calls/cpass:6.1f}")
def spearman(a,b):
    n=len(a); ra=sorted(range(n),key=lambda i:-a[i]); rb=sorted(range(n),key=lambda i:-b[i]); pa=[0]*n; pb=[0]*n
    for k,i in enumerate(ra): pa[i]=k
    for k,i in enumerate(rb): pb[i]=k
    return 1-6*sum((pa[i]-pb[i])**2 for i in range(n))/(n*(n*n-1))
for B in (8,16,32,48):
    have=[(g,cf[B]) for _,_,g,cf,_ in rows if B in cf]
    if len(have)>=5:
        agree=sum(1 for g,c in have if cls(g)==cls(c)); dec=[(g,c) for g,c in have if cls(g)!="neutral"]; sign=sum(1 for g,c in dec if (g>0)==(c>0))
        fk=sum(1 for g,c in have if cls(g)=="harmful" and c>3); fd=sum(1 for g,c in have if cls(g)=="helpful" and c<-3)
        print(f"B={B:2d}: components {len(have):2d} | Spearman {spearman([g for g,_ in have],[c for _,c in have]):.2f} | 3-class agreement {agree}/{len(have)} | sign agreement on decisive {sign}/{len(dec)} | false-keep {fk} false-drop {fd}")
fam={}
for name,kind,g,cf,n in rows:
    if 32 in cf: fam.setdefault(kind,[]).append((g,cf[32]))
for k,v in fam.items(): print(f"family {k:9s}: n={len(v)} sign agreement (decisive) {sum(1 for g,c in v if abs(g)>3 and (g>0)==(c>0))}/{sum(1 for g,c in v if abs(g)>3)}")
