import json, random, statistics as st, re
R="/net/scratch/ymeng3/bos_alfworld/results"; rng=random.Random(5)
def W(tag,n=48):
    d=json.load(open(f"{R}/{tag}_seed1.json")); return [1 if w else 0 for w in d["won"]][:n], d
def ci(a,b,B=4000):
    d=[x-y for x,y in zip(a,b)]; n=len(d); m=100*sum(d)/n; bs=sorted(100*sum(d[rng.randrange(n)] for _ in range(n))/n for _ in range(B)); return m,bs[int(.025*B)],bs[int(.975*B)]
out=[]
for lab,e,c,nofb in (("r6 E1 (unvisited-nav fallback)","r6_E1","PV_r6_C","PVA_r6_nofb"),("MECH07 E1","mech07_E1","XS_MECH07_C","XS_MECH07_nofb")):
    E,dE=W(e); C,_=W(c); N,_=W(nofb); m1,l1,h1=ci(E,C); m2,l2,h2=ci(E,N); ok=(m2>=-3 and m1>=5)
    out.append(f"{lab:32s} success E1 {100*st.mean(E):.1f}% C {100*st.mean(C):.1f}% C\\fb {100*st.mean(N):.1f}% | E1-C {m1:+.1f} [{l1:+.1f},{h1:+.1f}] | E1-C\\fb {m2:+.1f} [{l2:+.1f},{h2:+.1f}] | prediction (E1-C\\fb>=-3 & E1-C>=+5): {'PASS' if ok else 'FAIL'} | api_err {dE['api_errors']}")
E,dE=W("ctrl21_E2"); C,dC=W("XS_ctrl21_C"); N,_=W("XS_ctrl21_noretry"); m1,l1,h1=ci(E,C); m2,l2,h2=ci(E,N)
def nochange(d): return sum(1 for t in d["traj"][:48] for x in t if x.get("retry_n") and not x.get("retry_chg")), sum(1 for t in d["traj"][:48] for x in t if x.get("retry_n"))
nE,tE=nochange(dE); nC,tC=nochange(dC)
out.append(f"{'ctrl21 E2 (retry hint)':32s} success E2 {100*st.mean(E):.1f}% C {100*st.mean(C):.1f}% C\\retry {100*st.mean(N):.1f}% | E2-C {m1:+.1f} [{l1:+.1f},{h1:+.1f}] | E2-C\\retry {m2:+.1f} [{l2:+.1f},{h2:+.1f}] | retry-without-change {nE}/{tE} vs C {nC}/{tC} | prediction (drop>=50% & E2-C>=0): {'PASS' if (nE<=0.5*nC and m1>=0) else 'FAIL'} | api_err {dE['api_errors']}")
VERBS=("go to","open","close","take","move","put","heat","cool","clean","slice","use","look","examine","inventory"); tot=0; ext=0
for tag in ("r6_E1","mech07_E1","ctrl21_E2"):
    d=json.load(open(f"{R}/{tag}_seed1.json"))
    for t in d["traj"]:
        for x in t:
            raw=x.get("raw0","")
            if raw and "<action>" not in raw.lower():
                tot+=1; lines=[l.strip().strip('"\'`').lower() for l in raw.split("\n") if l.strip()]
                if any(l.startswith(VERBS) and len(l.split())<=6 for l in lines[-4:]): ext+=1
out.append(f"E3 material: reasoning-only first replies {tot}; with a command-like line among the last 4 lines {ext} ({100*ext/max(tot,1):.0f}%)")
txt="\n".join(out); print(txt); open("/net/scratch/ymeng3/bos_screens/hag/edits_result.txt","w").write(txt+"\n")
