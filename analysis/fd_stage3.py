"""Stage 3: rescue events -> isolated operators (OP_k, K=6) and search-only full candidates (SO_k, K=6)."""
import json, sys, collections
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag"); from fd_lib import *
meta = json.load(open(f"{R}/fd/meta.json")); hints = [json.load(open(f"{R}/fd/hints_{k}.json")) for k in range(4)]
C = json.load(open(f"{R}/results/XS_ctrl21_C_seed1.json")); traj = dict(zip(C["games_actual"], C["traj"]))
res = {}
for t in ["FD_ctrl"] + [f"FD_hint{k}" for k in range(4)]:
    d = json.load(open(f"{R}/results/{t}_seed1.json")); res[t] = dict(zip(d["games_actual"], d["won"]))
events = []
for g, m in meta.items():
    if res["FD_ctrl"].get(g): continue
    for k in range(4):
        if res[f"FD_hint{k}"].get(g): events.append({"game": g, "class": m["class"], "t": m["tstar"], "strategy": hints[k][g], "window": window(traj[g], m["tstar"])})
byc = collections.Counter(e["class"] for e in events); print("rescue events", len(events), dict(byc), flush=True)
json.dump(events, open(f"{R}/fd/events.json", "w"), indent=1)
ev_txt = "\n\n".join(f"[event {i+1}] failure class: {e['class']} | task family: {e['game'].split('/')[-3]}\nTrajectory before the failure point:\n{e['window']}\nSTRATEGY THAT RESCUED IT (from the same state): {e['strategy']}" for i, e in enumerate(events[:16]))
ctx_op = ("FAILURE-DRIVEN EVIDENCE. Below are failures of the current harness together with a strategy that, injected as advice from the failure state, "
          "turned the failure into a success. Write ONE ISOLATED OPERATOR: a small, self-contained change to the current patch that implements one of these strategies "
          "as a rule with an explicit applicability condition (when it fires) so that it fixes this failure class WITHOUT changing behaviour elsewhere. "
          "Add a line 'TARGET: <failure class it fixes and the condition>' before the code.\n\n" + ev_txt)
ops = propose_ops(ctx_op, 6, "OP", f"{R}/patches_fd", log_path=f"{R}/fd/op_log.json")
fails = [g for g, m in meta.items()][:12]
raw_txt = "\n\n".join(f"[failure {i+1}] task family: {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}" for i, g in enumerate(fails))
ctx_so = ("SEARCH-ONLY BASELINE. Below are failure trajectories of the current harness (no analysis, no rescue evidence). Propose ONE improved COMPLETE candidate patch "
          "(you may change anything in the hook API). Add a line 'TARGET: <what you are trying to fix>'.\n\n" + raw_txt)
sos = propose_ops(ctx_so, 6, "SO", f"{R}/patches_fd", log_path=f"{R}/fd/so_log.json")
print("operators", [p for p, _ in ops]); print("search-only", [p for p, _ in sos])
with open(f"{R}/fd/jobs_stage4.txt", "w") as f:
    f.write("XS_ctrl21_C patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py 2 48\n")
    for pid, p in ops + sos:
        for s in (1, 2): f.write(f"{pid} {p} {s} 48\n")
with open(f"{R}/fd/jobs_local.txt", "w") as f:
    for pid, p in ops: f.write(f"LOC_{pid} {p} 1\n")
print("spent", round(A.GUARD.spent(), 2))
