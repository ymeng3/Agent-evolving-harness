"""Offline trigger dry-run ($0): replay logged bare trajectories (Discovery s1) through each candidate's edits and count where they
would fire (pre_call changes the prompt, post_parse/pre_complete change the code, post_exec touches state). Screens dead edits before any pass."""
import json, os, sys, importlib
sys.path.insert(0, "/net/scratch/ymeng3/bos_appworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld")
R = "/net/scratch/ymeng3/bos_appworld"; os.environ.pop("BOS_EDITS_OFF", None)
import bos_appworld_v3 as V
b = json.load(open(f"{R}/results/CH27_F0_seed1.json")); cands = json.load(open(f"{R}/phase2/candidates.json"))
print(f"{'candidate':44s} fire_tasks/50  fire_steps  pre_call post_parse post_exec pre_complete  errors")
for c in cands:
    if not c["valid"]: continue
    try: active, off, funcs, legacy, consts = V.load_v3(c["path"])
    except Exception as e: print(c["pid"][:44], "load error", str(e)[:60]); continue
    ft = fs = 0; per = {"pre_call": 0, "post_parse": 0, "post_exec": 0, "pre_complete": 0}; errs = 0
    for tr in b["traj"]:
        state = {}; fired_task = False
        for s in tr:
            prompt = "Task: ...\nOutput:\n```\n" + (tr[s["step"]-1]["out"] if s["step"] > 0 else "") + "\n```"; code = s["code"]; fired = False
            for eid, f in funcs["pre_call"]:
                try: p2 = f(prompt, state); fired |= (p2 != prompt); per["pre_call"] += int(p2 != prompt)
                except Exception: errs += 1
            for eid, f in funcs["post_parse"]:
                try: c2 = f(code, state); ch = isinstance(c2, str) and c2.strip() and c2 != code; fired |= bool(ch); per["post_parse"] += int(bool(ch)); code = c2 if ch else code
                except Exception: errs += 1
            if "complete_task" in code:
                for eid, f in funcs["pre_complete"]:
                    try: c2 = f(code, state); ch = isinstance(c2, str) and c2.strip() and c2 != code; fired |= bool(ch); per["pre_complete"] += int(bool(ch))
                    except Exception: errs += 1
            for eid, f in funcs["post_exec"]:
                try: before = json.dumps(state, default=str, sort_keys=True); f(s["code"], s["out"], state); ch = json.dumps(state, default=str, sort_keys=True) != before; per["post_exec"] += int(ch)
                except Exception: errs += 1
            fs += int(fired); fired_task |= fired
        ft += int(fired_task)
    print(f"{c['pid'][:44]:44s} {ft:6d}/50      {fs:6d}     {per['pre_call']:8d} {per['post_parse']:10d} {per['post_exec']:9d} {per['pre_complete']:12d}  {errs}")
