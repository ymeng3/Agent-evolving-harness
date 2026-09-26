"""STEP 0 of the overnight tree: pooled seed 1+2 decision on the two frozen endpoints. Prints GATE PASS/FAIL. $0."""
import json, random, sys
R="/net/scratch/ymeng3/bos_alfworld/results"; rng=random.Random(2026)
def W(tag, seeds=(1,2)):
    out={}
    for s in seeds:
        d=json.load(open(f"{R}/{tag}_seed{s}.json")); assert d["api_errors"]==0, f"{tag} seed{s} api_errors={d['api_errors']}"
        for g,w in zip(d["games"],d["won"]): out[(s,g)]=1 if w else 0
    return out
F0=W("LQD_F0"); keys=sorted(F0); n=len(keys)
def dec(a,b,B=6000):
    d=[a[k]-b[k] for k in keys]; m=100*sum(d)/n; bs=sorted(100*sum(d[rng.randrange(n)] for _ in range(n))/n for _ in range(B))
    pk=sum(x>3 for x in bs)/B; pd=sum(x<-3 for x in bs)/B
    return m, bs[int(.025*B)], bs[int(.975*B)], ("KEEP" if pk>=.9 else "DROP" if pd>=.9 else "UNCERTAIN"), pk, pd
r4="P1B_ours_r4_structured_reasoning_wit"; r6="P1B_ours_r6_strategic_fallback_with_"
C4=W(f"{r4}_C"); C4H=W(f"{r4}_loo_HISTOR"); C4M=W(f"{r4}_loo_memory"); C4R=W(f"{r4}_loo_retry_")
C6=W(f"{r6}_C"); C6F=W(f"{r6}_loo_choose"); C6H=W(f"{r6}_loo_HISTOR")
lines=[f"POOLED seeds 1+2, {n} paired episodes, delta=3pp/90%"]
a=dec(C4,F0); b=dec(C4H,F0); g=dec(C4,C4H); m=dec(C4,C4M); r=dec(C4,C4R)
lines+= [f"r4: C vs F0 {a[0]:+.2f} [{a[1]:+.2f},{a[2]:+.2f}] {a[3]} | C\\HISTORY vs F0 {b[0]:+.2f} [{b[1]:+.2f},{b[2]:+.2f}] {b[3]} | gamma_HISTORY {g[0]:+.2f} [{g[1]:+.2f},{g[2]:+.2f}] {g[3]} | gamma_memory {m[0]:+.2f} {m[3]} | gamma_retry {r[0]:+.2f} {r[3]}"]
E1 = (b[3]=="KEEP" and a[3]!="KEEP")
c=dec(C6,F0); f=dec(C6,C6F); h=dec(C6,C6H); e=dec(C6F,F0)
lines+= [f"r6: C vs F0 {c[0]:+.2f} [{c[1]:+.2f},{c[2]:+.2f}] {c[3]} | gamma_fallback {f[0]:+.2f} [{f[1]:+.2f},{f[2]:+.2f}] {f[3]} (P(<-3)={f[5]:.2f}) | C\\fallback vs F0 {e[0]:+.2f} {e[3]} | gamma_HISTORY {h[0]:+.2f} {h[3]}"]
E2 = (f[3]=="DROP")
lines+= [f"E1 (r4 subset KEEP while whole not KEEP): {E1}   E2 (r6 fallback DROP): {E2}", "GATE " + ("PASS" if (E1 or E2) else "FAIL")]
print("\n".join(lines)); open("/net/scratch/ymeng3/bos_screens/hag/p1b_pool_result.txt","w").write("\n".join(lines)+"\n")
sys.exit(0 if (E1 or E2) else 1)
