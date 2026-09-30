"""Rescue round 2 on AppWorld challenge: for each task lost in CH27_F0 seed 1, branch before the first state-changing call,
ask the local 27B for K=3 distinct strategies from that state; write replay.json, tasks.json, hints_k.json, meta.json."""
import json, re, sys, os
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_appworld"; K = 3; bb = A.Backbone(0.7); r = json.load(open(f"{R}/results/CH27_F0_seed1.json"))
MUT = re.compile(r"apis\.(?!api_docs|supervisor)\w+\.(create|update|delete|send|add|remove|withdraw|pay|post|mark|reply|like|unlike|set|transfer|book|cancel|upload|buy|order|move|archive|label|change)\w*\(")
os.environ["APPWORLD_ROOT"] = "/net/scratch/ymeng3/appworld_v2"
from appworld import AppWorld
rep = {}; meta = {}; hints = [{} for _ in range(K)]; tasks = []
for t, w, G, tr in zip(r["games"], r["won"], r["G"], r["traj"]):
    if w: continue
    acts = [s["code"] for s in tr]; mut = [i for i, c in enumerate(acts) if MUT.search(c)]; errs = [i for i, s in enumerate(tr) if s["exec_error"]]
    t_b = mut[0] if mut else (errs[0] if errs else max(0, len(tr) - 3)); rep[t] = acts[:t_b]; tasks.append(t)
    with AppWorld(task_id=t, experiment_name="gen_alts", random_seed=1) as w_: instr = w_.task.instruction
    meta[t] = {"G_f0": G, "t_branch": t_b, "len": len(tr), "instruction": instr}
    tail = "\n".join(f"[cell {i}] {tr[i]['code'][:220]}\n -> {tr[i]['out'][:160]}" for i in range(max(0, t_b - 4), min(len(tr), t_b + 4)))
    p = (f"An agent that writes python cells calling app APIs FAILED this task.\nTASK: {instr}\nCells around the point where it went wrong (cell {t_b}):\n{tail}\n\n"
         f"Propose {K} DISTINCT, concrete strategies for what the agent should do from cell {t_b} onward to complete the task correctly: which APIs/apps to use or avoid, how to select the right items, what to verify before finishing. "
         f"Each 1-3 sentences, actionable, and the {K} must differ in approach. Reply with ONLY a JSON list of strings.")
    resp, err = bb.call(p); m = re.search(r"\[.*\]", resp or "", re.S)
    try: L = json.loads(m.group(0)); assert len(L) >= K
    except Exception: L = ["List the app's APIs first and pick the one whose description matches the task verb exactly; read its doc before calling.", "Fetch ALL pages of results before filtering; apply every constraint in the task (price, rating, size, count, address) explicitly in code and print the filtered list before acting.", "Before complete_task, re-read the task and check each requirement against printed API results; fix anything missing."]
    for k in range(K): hints[k][t] = str(L[k])[:400]
    print(t, "branch", t_b, "|", str(L[0])[:100], flush=True)
json.dump(rep, open(f"{R}/night/replay.json", "w")); json.dump(tasks, open(f"{R}/night/tasks.json", "w")); json.dump(meta, open(f"{R}/night/meta.json", "w"), indent=1)
for k in range(K): json.dump(hints[k], open(f"{R}/night/hints_{k}.json", "w"), indent=1)
print("failures", len(tasks), "calls", bb.calls, "errors", bb.errors)
