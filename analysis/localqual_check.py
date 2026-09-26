# Frozen rule: hag/LOCAL_BACKEND_QUALIFICATION.md (A1 |F0-0.3229|<=0.05; A2 HR-F0>=+8pp; A3 MECH07-F0<=-5pp), 3 seeds each.
import json, sys, statistics as st
R="/net/scratch/ymeng3/bos_alfworld/results"
def m(tag):
    v=[json.load(open(f"{R}/{tag}_seed{s}.json")) for s in (1,2,3)]
    assert all(x["model"]=="qwen/qwen3-30b-a3b-instruct-2507" for x in v), "served model id mismatch"
    return st.mean(x["success_rate"] for x in v), [round(x["success_rate"],4) for x in v]
f0,f0s=m("LQ_F0"); hr,hrs=m("LQ_HR"); mk,mks=m("LQ_MECH07")
a1=abs(f0-0.3229)<=0.05; a2=(hr-f0)*100>=8; a3=(mk-f0)*100<=-5
print(f"F0 {f0:.4f} {f0s} | HR {hr:.4f} {hrs} | MECH07 {mk:.4f} {mks}")
print(f"A1 |F0-0.3229|={abs(f0-0.3229):.4f} {'PASS' if a1 else 'FAIL'} | A2 HR-F0={100*(hr-f0):+.2f}pp {'PASS' if a2 else 'FAIL'} | A3 MECH07-F0={100*(mk-f0):+.2f}pp {'PASS' if a3 else 'FAIL'}")
print("QUALIFICATION", "PASS" if a1 and a2 and a3 else "FAIL")
