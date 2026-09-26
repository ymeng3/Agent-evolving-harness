"""Stage 5: credit-guided inheritance -> OURS patch; pick best search-only; write held-out jobs."""
import json, sys, os, glob, re
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag"); from fd_lib import *
ops = sorted(glob.glob(f"{R}/patches_fd/OP*.py")); sos = sorted(glob.glob(f"{R}/patches_fd/SO*.py"))
def sr(t, s):
    f = f"{R}/results/{t}_seed{s}.json"; return json.load(open(f))["success_rate"] * 100 if os.path.exists(f) else None
c = [sr("XS_ctrl21_C", 1), sr("XS_ctrl21_C", 2)]; meta = json.load(open(f"{R}/fd/meta.json"))
rows = []; committed = []
print(f"C train48: {c}")
for p in ops + sos:
    pid = os.path.basename(p)[:-3]; v = [sr(pid, 1), sr(pid, 2)]
    if None in v or None in c: print(pid, "missing"); continue
    net = [a - b for a, b in zip(v, c)]; loc = None
    f = f"{R}/results/LOC_{pid}_seed1.json"
    if os.path.exists(f): d = json.load(open(f)); loc = sum(d["won"])
    ok = pid.startswith("OP") and min(net) >= 3.0
    rows.append((pid, v, net, loc, ok)); committed += [p] if ok else []
    print(f"{pid:40s} train48 {v} net {[round(x,1) for x in net]} local-fix {loc} {'COMMIT' if ok else ''}")
so_best = max([r for r in rows if r[0].startswith("SO")], key=lambda r: sum(r[2]), default=None)
os.makedirs(f"{R}/patches_fd/final", exist_ok=True)
if len(committed) == 0: ours = f"{R}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py"; print("no operator committed -> OURS = C")
elif len(committed) == 1: ours = committed[0]
else:
    ctx = "MERGE these committed operators into ONE complete patch that keeps each rule (they were each validated independently). Output the merged module.\n\n" + "\n\n".join(f"```python\n{open(p).read()}\n```" for p in committed)
    m = propose_ops(ctx, 1, "MERGED", f"{R}/patches_fd/final", log_path=f"{R}/fd/merge_log.json", temperature=0.3)
    ours = m[0][1] if m else committed[0]
open(f"{R}/fd/ours_path.txt", "w").write(ours); print("OURS =", ours, "| committed", [os.path.basename(p) for p in committed], "| SO best", so_best[0] if so_best else None)
with open(f"{R}/fd/jobs_heldout.txt", "w") as f:
    for s in (1, 2):
        f.write(f"HO_C patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py {s} 48\n"); f.write(f"HO_OURS {ours} {s} 48\n")
        if so_best: f.write(f"HO_SO {R}/patches_fd/{so_best[0]}.py {s} 48\n")
json.dump({"rows": rows, "committed": committed, "so_best": so_best[0] if so_best else None, "ours": ours}, open(f"{R}/fd/stage5.json", "w"), indent=1)
