"""RawDiagnoser: gpt-4o produces a FailureMechanism for each Discovery failure (seed 1 logs), then groups them into a mechanism bank."""
import json, os, re, sys, collections
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_appworld/phase2"); import bos_alfworld as A; from schema import *
R = "/net/scratch/ymeng3/bos_appworld"; os.environ["APPWORLD_ROOT"] = "/net/scratch/ymeng3/appworld_v2"
from appworld import AppWorld
def window(tr, lo, hi): return "\n".join(f"[cell {s['step']}] {s['code'][:260]}\n -> {s['out'][:200]}" for s in tr[lo:hi])
r = json.load(open(f"{R}/results/CH27_F0_seed1.json")); bank = []
for t, w, G, tr in zip(r["games"], r["won"], r["G"], r["traj"]):
    if w: continue
    with AppWorld(task_id=t, experiment_name="diag", random_seed=1) as w_: instr = w_.task.instruction
    n = len(tr); mid = max(0, n - 12)
    txt = f"TASK: {instr}\nOUTCOME: failed; goal checks passed {G or 0:.2f}; {n} cells; {'completed' if any('complete_task' in s['code'] for s in tr) else 'never called complete_task'}.\nFIRST CELLS:\n{window(tr, 0, 4)}\nLAST CELLS:\n{window(tr, mid, n)}"
    try: resp = A.gpt4o([{"role": "system", "content": FM_PROMPT}, {"role": "user", "content": txt + "\n\nReply with ONLY the JSON object."}], temperature=0.2, max_tokens=700)
    except Exception as e: print(t, "error", str(e)[:80]); continue
    m = re.search(r"\{.*\}", resp, re.S)
    try: fm = json.loads(m.group(0))
    except Exception: print(t, "unparsable"); continue
    fm = {k: fm.get(k, "") for k in FM_FIELDS}; fm["task"] = t; fm["instruction"] = instr; fm["G"] = G; bank.append(fm)
    print(t, "|", fm["capability"], "/", fm["implementation"], "@", fm["control_point"], "|", str(fm["mechanism"])[:90], flush=True)
json.dump(bank, open(f"{R}/phase2/failure_bank.json", "w"), indent=1)
c = collections.Counter((fm["capability"], fm["implementation"]) for fm in bank); print("\naddress counts:", c.most_common()); print("spent", round(A.GUARD.spent(), 2))
