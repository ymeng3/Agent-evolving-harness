"""Audits A (trigger sparsity) and B (reusable-prefix fraction) from step-logged passes. Usage: auditAB.py TAG..."""
import json, sys
R="/net/scratch/ymeng3/bos_alfworld/results"
for tag in sys.argv[1:]:
    d=json.load(open(f"{R}/{tag}_seed1.json")); N=len(d["traj"]); tot_calls=sum(x.get("calls",1) for t in d["traj"] for x in t)
    print(f"\n{tag}: {N} games, success {100*d['success_rate']:.1f}%, total LLM calls {tot_calls}")
    for comp,key in (("retry(changed action)","retry_chg"),("fallback","fb"),("parse(changed)","parse_chg")):
        ep_trig=0; acts=0; pre_calls=0; pre_frac=[]
        for t in d["traj"]:
            steps=[x for x in t if x.get(key)]
            if steps:
                ep_trig+=1; acts+=len(steps); first=steps[0]["step"]
                cb=sum(x.get("calls",1) for x in t if x["step"]<first); ca=sum(x.get("calls",1) for x in t); pre_calls+=cb; pre_frac.append(cb/max(ca,1))
        print(f"  {comp:22s} episodes with activation {ep_trig:3d}/{N} ({100*ep_trig/N:4.1f}%)  activations {acts:4d}  | Audit B: reusable prefix (LLM calls before first activation) mean {100*(sum(pre_frac)/len(pre_frac) if pre_frac else 0):4.1f}% of the episode; over all {N} episodes an OFF-branch replay would skip {100*(1 - (tot_calls - pre_calls - sum(sum(x.get('calls',1) for x in t) for t in d['traj'] if not any(x.get(key) for x in t))*0)/tot_calls):.0f}% ... see waterfall below")
        # waterfall: cost of a full LOO pass = tot_calls; trigger-conditioned = only episodes with activation; + prefix replay = only calls after first activation
        act_ep_calls=sum(sum(x.get("calls",1) for x in t) for t in d["traj"] if any(x.get(key) for x in t))
        post=act_ep_calls-pre_calls
        print(f"      waterfall (LLM calls): full LOO {tot_calls} -> trigger-conditioned {act_ep_calls} ({100*act_ep_calls/tot_calls:.0f}%) -> + prefix replay {post} ({100*post/tot_calls:.0f}%)")
