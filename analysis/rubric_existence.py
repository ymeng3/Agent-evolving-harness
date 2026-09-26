import json, re, statistics as st, sys
R="/net/scratch/ymeng3/bos_alfworld/results"
def dims(d):
    T=d["traj"]; won=d["won"]; N=len(T)
    inv=rec=inv_n=steps=0; loops=0; breadth=[]; sw=[]; maxed=0
    for i,t in enumerate(T):
        acts=[x["action"] for x in t]; steps+=len(t)
        vs=[x["valid"] for x in t]; inv+=sum(1 for v in vs if not v)
        for j in range(len(vs)-1):
            if not vs[j]: inv_n+=1; rec+=int(vs[j+1])
        loops+=int(any(acts[j]==acts[j-1]==acts[j-2] for j in range(2,len(acts))))
        gos={a for a in acts if a.startswith("go to")}; breadth.append(len(gos)/max(len(t),1))
        if won[i]: sw.append(len(t))
        maxed+=int(len(t)>=50)
    return {"succ":100*sum(won)/N,"invalid":100*inv/steps,"recover":100*rec/max(inv_n,1),"loop":100*loops/N,
            "breadth":100*st.mean(breadth),"steps_win":st.mean(sw) if sw else float("nan"),"maxed":100*maxed/N}
def load(tag,seeds=(1,2,3)):
    v=[dims(json.load(open(f"{R}/{tag}_seed{s}.json"))) for s in seeds]
    return {k:[x[k] for x in v] for k in v[0]}
sets={"API":["F0","N04_optimize_history_length","N03_retry_with_reasoning","E1_HR_hist10_retry_basetemp","G_MECH07_plan_sub_goal_completion"],
      "LOCAL":["LQ_F0","LQ_HR","LQ_MECH07"]}
K=["succ","invalid","recover","loop","breadth","steps_win","maxed"]
for name,tags in sets.items():
    base=load(tags[0]); print(f"\n== {name} ==  F0 seed spread (max-min): "+" ".join(f"{k}={max(base[k])-min(base[k]):.1f}" for k in K))
    print(f"{'tag':34s}"+"".join(f"{k:>11s}" for k in K))
    print(f"{tags[0]:34s}"+"".join(f"{st.mean(base[k]):11.1f}" for k in K))
    for t in tags[1:]:
        v=load(t); print(f"{t[:34]:34s}"+"".join(f"{st.mean(v[k])-st.mean(base[k]):+11.1f}" for k in K)+"   (delta vs F0)")
