"""SciWorld verifier test (SCIWORLD_VERIFIER_FROZEN.md). Episode-paired by manifest index (no permutation in this harness)."""
import json, statistics as st, random
R="/net/scratch/ymeng3/bos_sciworld/results"; rng=random.Random(3)
def load(t): return json.load(open(f"{R}/{t}_seed1.json"))
F=load("SW_F0"); out=[f"F0: success {100*F['success_rate']:.1f}% mean score {F['mean_score']:.1f}; invalid-output rate {100*sum(1 for t in F['traj'] for x in t if not x['admissible'])/sum(len(t) for t in F['traj']):.0f}%"]
def ci(d,B=3000):
    n=len(d); m=st.mean(d); bs=sorted(st.mean(d[rng.randrange(n)] for _ in range(n)) for _ in range(B)); return m,bs[int(.025*B)],bs[int(.975*B)]
for tag,key,lab in (("SW_retry","retry_chg","retry"),("SW_fb","fb","fallback 'look around'"),("SW_hist10",None,"history10")):
    D=load(tag); ds=[a-b for a,b in zip(D["score"],F["score"])]; dw=[int(a)-int(b) for a,b in zip(D["won"],F["won"])]
    m,lo,hi=ci(ds); mw,lw,hw=ci(dw); inv=100*sum(1 for t in D["traj"] for x in t if not x["admissible"])/sum(len(t) for t in D["traj"])
    line=f"{lab:22s} LOO mean-score {m:+6.1f} [{lo:+.1f},{hi:+.1f}] | LOO success {100*mw:+5.1f}pp [{100*lw:+.1f},{100*hw:+.1f}] | success {100*D['success_rate']:.1f}% | invalid-output {inv:.0f}%"
    if key:
        acts=0; gain_after=[]; base=[]
        for t in D["traj"]:
            steps={x["step"]:x for x in t}
            for x in t:
                if x.get(key):
                    acts+=1; g=sum(steps[s]["dscore"] for s in range(x["step"],min(x["step"]+3,len(t))) if s in steps); gain_after.append(g)
            act_steps={x["step"] for x in t if x.get(key)}; nb=[x["dscore"] for x in t if x["step"] not in act_steps]
            if nb: base.append(st.mean(nb)*3)
        V=(st.mean(gain_after) if gain_after else 0)-(st.mean(base) if base else 0)
        line+=f" | activations {acts} | V (3-step gain after activation minus baseline) = {V:+.2f} -> {'agrees' if (V>0)==(m>0) else 'DISAGREES'} with LOO sign"
    else:
        on=[t for t in D["traj"]]; off=F["traj"]
        r_on=st.mean(1 for t in on if any(x["dscore"]>0 for x in t))/1 if False else sum(1 for t in on if any(x["dscore"]>0 for x in t))/len(on); r_off=sum(1 for t in off if any(x["dscore"]>0 for x in t))/len(off)
        f_on=st.mean([next((x["step"] for x in t if x["dscore"]>0),40) for t in on]); f_off=st.mean([next((x["step"] for x in t if x["dscore"]>0),40) for t in off])
        T=(r_on-r_off)+(f_off-f_on)/40; line+=f" | T (reach + timing) = {T:+.3f} -> {'agrees' if (T>0)==(m>0) else 'disagrees'} with LOO sign (expected, not required)"
    out.append(line)
print("\n".join(out)); open("/net/scratch/ymeng3/bos_screens/hag/sciworld_result.txt","w").write("\n".join(out)+"\n")
