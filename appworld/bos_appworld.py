#!/usr/bin/env python3
"""BENCHMARK OPPORTUNITY SEARCH — AppWorld natural-candidate screen (2026-09-08). Guard 'bos_appworld' $30 hard cap.
Harness = official SimplifiedReActCodeAgent + gpt-4o-mini (appworld_v2), hook = prompt addendum appended to the official
react_code_agent instructions (the same hook as the aggressive probe). Tasks = 50 pre-declared test_normal d1/d2 tasks
(tasks50.json, sorted ids). Two trials per arm: model seed 100 / 101, temperature 0. Metric G (goal tests passed fraction)
and H (harm tests failed fraction); screen value = G (H reported).  Usage: eval --prompt P|official --tag T --seed S | propose"""
import os, sys, json, time, argparse, hashlib, re, urllib.request, traceback
os.environ["APPWORLD_ROOT"] = "/net/scratch/ymeng3/appworld_v2"; os.environ.setdefault("TMPDIR", "/net/scratch/ymeng3/pip_tmp")
KEY = os.environ.get("OPENROUTER_API_KEY") or open(os.path.expanduser("~/.config/openrouter/key")).read().strip(); os.environ["OPENROUTER_API_KEY"] = KEY; os.environ.setdefault("OPENAI_API_KEY", "sk-dummy-not-used-litellm-openrouter")
sys.path.insert(0, "/net/scratch/ymeng3/metaharness_runs/level4"); from finalB_guard import SpendGuard
OUT = "/net/scratch/ymeng3/bos_appworld"; REPO = "/net/scratch/ymeng3/appworld_repo"; OFFICIAL = REPO + "/experiments/prompts/react_code_agent/instructions.txt"
GUARD = SpendGuard("bos_appworld", 30.0, f"{OUT}/guard_state.json"); TASKS = json.load(open(f"{OUT}/tasks50.json"))
COST_PER_TOKEN = {"input_cache_hit": 7.5e-08, "input_cache_miss": 1.5e-07, "input_cache_write": 0.0, "output": 6e-07}

def make_config(prompt_path, seed):
    return {"type": "simplified_react_code_agent",
            "model_config": {"client_name": "litellm", "api_type": "chat_completions", "name": "openrouter/openai/gpt-4o-mini", "temperature": 0.0, "seed": seed,
                             "drop_reasoning_content": False, "cost_per_token": COST_PER_TOKEN, "retry_after_n_seconds": 8, "use_cache": False, "max_retries": 6},
            "appworld_config": {"random_seed": seed, "raise_on_extra_parameters": True}, "logger_config": {"color": False, "verbose": False},
            "usage_tracker_config": {"max_cost_overall": 30.0, "max_cost_per_task": 0.15, "max_output_tokens_per_task": 100000},
            "prompt_file_path": prompt_path, "ignore_multiple_calls": True, "max_prompt_length": None, "max_output_length": None, "max_steps": 50,
            "log_lm_calls": False, "skip_if_finished": False}

def evaluate_GH(world):
    d = world.evaluate().to_dict()
    gp = sum(1 for x in d["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in d["failures"] if x.get("label") == "no_op_fail")
    sp = sum(1 for x in d["passes"] if x.get("label") == "no_op_pass"); sf = sum(1 for x in d["failures"] if x.get("label") == "no_op_pass")
    return dict(G=(gp / (gp + gf) if gp + gf else None), H=(sf / (sp + sf) if sp + sf else 0.0), gp=gp, gf=gf, sp=sp, sf=sf, success=d.get("success"))

def run_eval(prompt, tag, seed):
    from appworld import AppWorld
    from appworld.task import Task
    from appworld_agents.code.simplified.agent import Agent, ExecutionIO
    path = OFFICIAL if prompt == "official" else prompt; exp = f"bos_{tag}_s{seed}"
    out = f"{OUT}/results/{tag}_seed{seed}.json"; rows = json.load(open(out))["rows"] if os.path.exists(out) else {}
    GUARD.baseline(); Task.load(task_id=TASKS[0]); agent = Agent.from_dict(make_config(path, seed)); t0 = time.time()
    for i, tid in enumerate(TASKS, 1):
        if tid in rows: continue
        GUARD.check(); agent.usage_tracker.reset(tid); steps = 0
        try:
            with AppWorld(task_id=tid, experiment_name=exp, **agent.appworld_config) as world:
                outs = []; agent.initialize(world)
                for _ in range(agent.max_steps):
                    agent.step_number += 1; steps += 1
                    ins, usage, status = agent.next_execution_inputs_usage_and_status(outs)
                    if status.failed: break
                    res = world.batch_execute([x.content for x in ins]); outs = [ExecutionIO(content=o, metadata=x.metadata) for x, o in zip(ins, res)]
                    agent.usage_tracker.add(tid, usage)
                    if world.task_completed() or agent.usage_tracker.exceeded(tid): break
                ev = evaluate_GH(world)
        except Exception as e:
            traceback.print_exc(); ev = dict(G=None, H=None, err=f"{type(e).__name__}: {e}")
        ev["steps"] = steps; rows[tid] = ev
        json.dump({"tag": tag, "seed": seed, "prompt": path, "rows": rows, "spent_guard": round(GUARD.spent(), 3), "wall": round(time.time() - t0)}, open(out, "w"), indent=1)
        print(f"[{i:2}/50] {tid} G={ev.get('G')} H={ev.get('H')} steps={steps} guard ${GUARD.spent():.2f}", flush=True)
    G = [r["G"] for r in rows.values() if r.get("G") is not None]; H = [r["H"] for r in rows.values() if r.get("H") is not None]
    print(f"DONE {tag} seed{seed}: meanG {sum(G)/len(G):.3f} meanH {sum(H)/len(H):.3f} n={len(G)} spent ${GUARD.spent():.2f}", flush=True)

def f0_profile():
    import glob, statistics as st
    R = [json.load(open(f)) for f in sorted(glob.glob(f"{OUT}/results/F0_seed*.json"))]; assert R
    G = [r["G"] for x in R for r in x["rows"].values() if r.get("G") is not None]; H = [r["H"] for x in R for r in x["rows"].values() if r.get("H") is not None]
    hp = {r["task"]: r for r in json.load(open("/net/scratch/ymeng3/appworld_data/harm_pool_full.json"))}
    by_app = {}
    for x in R:
        for tid, r in x["rows"].items():
            if r.get("G") is None: continue
            for a in hp[tid]["apps"]: by_app.setdefault(a, []).append(r["G"])
    return {"trials": len(R), "meanG": round(st.mean(G), 3), "meanH": round(st.mean(H), 3), "frac_full_success": round(sum(1 for g in G if g == 1.0) / len(G), 3),
            "frac_zero": round(sum(1 for g in G if g == 0.0) / len(G), 3), "mean_steps": round(st.mean([r["steps"] for x in R for r in x["rows"].values()]), 1),
            "frac_max_steps": round(sum(1 for x in R for r in x["rows"].values() if r["steps"] >= 50) / len(G), 3), "G_by_app": {a: round(st.mean(v), 2) for a, v in by_app.items()}}

PROPOSER_SYS = ("You are improving an LLM agent harness for AppWorld (the agent writes Python code that calls app APIs to complete personal-assistant "
                "tasks; goal tests check the resulting state; harm tests check that unrelated state was not modified). The ONLY hook you may change is an "
                "ADDENDUM block appended to the end of the agent's instruction prompt. Respond with exactly:\nNAME: <short_snake_case>\nADDENDUM: <at most 120 words>")

def propose(K=10):
    prof = f0_profile(); base = open(OFFICIAL).read(); cands = []; log = []; att = 0
    while len(cands) < K and att < 2 * K:
        att += 1; GUARD.check()
        user = (f"[attempt {att}]\nBASELINE (F0) PROFILE on 50 tasks: {json.dumps(prof)}\n\nThe current instruction prompt ends with:\n...{base[-1500:]}\n\n"
                f"Earlier proposal names (do not repeat their idea): {json.dumps([c['name'] for c in cands])}\n\nPropose ONE new addendum expected to raise goal completion without modifying unrelated state.")
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                                     data=json.dumps({"model": "openai/gpt-4o", "messages": [{"role": "system", "content": PROPOSER_SYS}, {"role": "user", "content": user}], "temperature": 1.0, "max_tokens": 500}).encode())
        with urllib.request.urlopen(req, timeout=120) as r: resp = json.loads(r.read().decode())["choices"][0]["message"]["content"]
        nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp); ad = re.search(r"ADDENDUM:\s*(.*)", resp, re.S)
        log.append({"attempt": att, "resp": resp})
        if not (nm and ad): continue
        name = f"N{len(cands)+1:02d}_{nm.group(1)[:40]}"; text = ad.group(1).strip(); p = f"{OUT}/prompts/{name}.txt"
        open(p, "w").write(base.rstrip() + "\n\nADDITIONAL DIRECTIVE:\n" + text + "\n"); cands.append({"name": name, "text": text, "path": p})
    frozen = {"created": time.strftime("%Y-%m-%d %H:%M"), "f0_profile": prof, "candidates": cands, "tasks_sha": hashlib.sha256(json.dumps(TASKS).encode()).hexdigest()[:16],
              "candidates_sha": hashlib.sha256(json.dumps([c["text"] for c in cands]).encode()).hexdigest()[:16], "seeds": [100, 101], "executor": "openrouter/openai/gpt-4o-mini T=0", "proposer_log": log, "spent": round(GUARD.spent(), 3)}
    json.dump(frozen, open(f"{OUT}/bos_appworld_frozen.json", "w"), indent=1)
    print(f"FREEZE ECHO: {len(cands)} candidates sha {frozen['candidates_sha']} tasks sha {frozen['tasks_sha']} spent ${frozen['spent']}")
    for c in cands: print(f"  {c['name']}: {c['text'][:140]}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--prompt", default="official"); ap.add_argument("--tag", default="F0"); ap.add_argument("--seed", type=int, default=100); a = ap.parse_args()
    run_eval(a.prompt, a.tag, a.seed) if a.cmd == "eval" else propose()
