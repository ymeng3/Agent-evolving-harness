"""Evolving-rubric minimal test: same proposer/base/K, only the diagnostic input differs. A raw | B fixed rubric | C evolved rubric.
Judge and proposer = gpt-4o. Discovery set = FD failures (+ rescue events). Writes patches_rubric/{A,B,C}k and held-out jobs."""
import json, sys, os, re
sys.path.insert(0, "/net/scratch/ymeng3/bos_screens/hag"); from fd_lib import *
meta = json.load(open(f"{R}/fd/meta.json")); C = json.load(open(f"{R}/results/XS_ctrl21_C_seed1.json")); traj = dict(zip(C["games_actual"], C["traj"]))
events = json.load(open(f"{R}/fd/events.json")) if os.path.exists(f"{R}/fd/events.json") else []
fails = list(meta)[:12]; disc = list(meta)[12:]   # 12 failures shown to the proposer; the rest (+events) are the rubric discovery set
raw = "\n\n".join(f"[failure {i+1}] task family: {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}" for i, g in enumerate(fails))
FIXED = ("RUBRIC (fixed):\n1. Action validity: are actions admissible / well-formed?\n2. Progress: do the steps discover new locations, objects or clues and move toward the goal?\n"
         "3. Efficiency: repetition, wasted steps, loops.\nFor each dimension give PASS/WARN/FAIL with a one-line evidence quote from the trajectory.")
def diagnose(rubric, g):
    p = f"Diagnose this failed household-agent trajectory with the rubric.\n{rubric}\n\nTask family: {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}\n\nOutput the per-dimension verdicts only."
    try: return A.gpt4o([{"role": "user", "content": p}], temperature=0.2, max_tokens=500)
    except Exception as e: return f"(judge error {str(e)[:60]})"
# --- C: evolve the rubric on the discovery set (ADD / REFINE / MERGE / PRUNE), 2 rounds
rubric = FIXED; log = []
for rnd in range(2):
    sample = disc[rnd*6:(rnd+1)*6]; diags = [(g, diagnose(rubric, g)) for g in sample]
    ev = "\n\n".join(f"[rescued case] class {e['class']}\n{e['window']}\nstrategy that fixed it: {e['strategy']}" for e in events[rnd*4:(rnd+1)*4])
    p = (f"You maintain a diagnostic rubric for failures of an LLM household agent. Current rubric:\n{rubric}\n\nHere are failures diagnosed with it:\n" +
         "\n\n".join(f"[case] {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}\nDIAGNOSIS: {d}" for g, d in diags) +
         (f"\n\nAnd cases where a specific strategy rescued the failure:\n{ev}" if ev else "") +
         "\n\nWhich failure mechanisms does the rubric MISS or blur (cases where every dimension says PASS/WARN yet the task failed, or two different mechanisms get the same verdict)? "
         "Propose rubric edits: ADD (new dimension with evaluation rule + evidence to use), REFINE (split a broad one), MERGE, PRUNE (a dimension that never separates cases). Keep at most 5 dimensions. "
         "Output the NEW rubric in the same format, then a line 'CHANGES: ...'.")
    try: r = A.gpt4o([{"role": "user", "content": p}], temperature=0.5, max_tokens=900)
    except Exception as e: r = rubric + f"\nCHANGES: (error {str(e)[:60]})"
    rubric = r.split("CHANGES:")[0].strip() or rubric; log.append({"round": rnd, "rubric": rubric, "changes": r.split("CHANGES:")[-1][:600]})
json.dump(log, open(f"{R}/rubric/evolution_log.json", "w"), indent=1); open(f"{R}/rubric/evolved_rubric.txt", "w").write(rubric)
print("EVOLVED RUBRIC:\n", rubric, "\nCHANGES:", [l["changes"][:200] for l in log], flush=True)
# --- diagnoses for B and C on the 12 shown failures
diagB = {g: diagnose(FIXED, g) for g in fails}; diagC = {g: diagnose(rubric, g) for g in fails}
ctxA = "FAILURE TRAJECTORIES of the current harness:\n\n" + raw + "\n\nPropose ONE change that fixes a failure mechanism you see. Add a line 'TARGET: ...'."
ctxB = "FAILURE TRAJECTORIES with a rubric diagnosis:\n\n" + "\n\n".join(f"[failure {i+1}] task family: {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}\nDIAGNOSIS ({'fixed rubric'}):\n{diagB[g]}" for i, g in enumerate(fails)) + "\n\nPropose ONE change that fixes a diagnosed failure mechanism. Add a line 'TARGET: ...'."
ctxC = f"FAILURE TRAJECTORIES with a rubric diagnosis. Rubric:\n{rubric}\n\n" + "\n\n".join(f"[failure {i+1}] task family: {g.split('/')[-3]}\n{window(traj[g], meta[g]['tstar'])}\nDIAGNOSIS:\n{diagC[g]}" for i, g in enumerate(fails)) + "\n\nPropose ONE change that fixes a diagnosed failure mechanism. Add a line 'TARGET: ...'."
out = {}
for lab, ctx in (("A", ctxA), ("B", ctxB), ("C", ctxC)):
    out[lab] = propose_ops(ctx, 6, f"RB{lab}", f"{R}/patches_rubric", log_path=f"{R}/rubric/prop_{lab}.json"); print(lab, [p for p, _ in out[lab]], flush=True)
with open(f"{R}/rubric/jobs_heldout.txt", "w") as f:
    for s in (1, 2):
        f.write(f"RB_C patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py {s} 48\n")
        for lab in out:
            for pid, p in out[lab]: f.write(f"{pid} {p} {s} 48\n")
print("spent", round(A.GUARD.spent(), 2))
