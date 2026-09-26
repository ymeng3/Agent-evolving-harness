"""LINE 3: AppWorld ReAct-code harness with the SAME 5-hook patch API as bos_alfworld (format_prompt, parse_action, retry_policy,
memory_update, choose_fallback; constants HISTORY_LENGTH, TEMPERATURE). Local backbone via BOS_BASE_URL. Per-step log: code,
output, exec_error, goal tests passed/failed (world.evaluate() every step = mid-episode verifier facts), component flags.
Usage: eval --patch P|none --seed S --tag T [--n-games N] [--workers W]"""
import os, sys, json, re, time, argparse, threading
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
os.environ["APPWORLD_ROOT"] = "/net/scratch/ymeng3/appworld_v2"; os.environ.setdefault("TMPDIR", "/net/scratch/ymeng3/pip_tmp")
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
OUT = "/net/scratch/ymeng3/bos_appworld"; TASKS = json.load(open(os.environ.get("BOS_TASKS", f"{OUT}/tasks50.json")))
INSTR = open("/net/scratch/ymeng3/appworld_repo/experiments/prompts/react_code_agent/instructions.txt").read()
MAX_STEPS = int(os.environ.get("BOS_AW_STEPS", "30"))
REPLAY = json.load(open(os.environ["BOS_REPLAY"])) if os.environ.get("BOS_REPLAY") else {}
HINTS = json.load(open(os.environ["BOS_HINTS"])) if os.environ.get("BOS_HINTS") else {}
def demo_messages(sup):
    txt = INSTR.replace("{{ main_user.first_name }}", sup.first_name).replace("{{ main_user.last_name }}", sup.last_name).replace("{{ main_user.email }}", sup.email).replace("{{ main_user.phone_number }}", sup.phone_number)
    msgs = []; role = None; buf = []
    for line in txt.split("\n"):
        if line.strip() in ("USER:", "ASSISTANT:"):
            if role: msgs.append({"role": role, "content": "\n".join(buf).strip()})
            role = "user" if line.strip() == "USER:" else "assistant"; buf = []
        else: buf.append(line)
    if role: msgs.append({"role": role, "content": "\n".join(buf).strip()})
    return msgs
def extract_code(resp):
    m = re.search(r"```python\s*(.*?)```", resp, re.S) or re.search(r"```\s*(.*?)```", resp, re.S)
    return m.group(1).strip() if m else ""
_PLAY = None
def _call(i): return _PLAY(i)
def run_eval(patch_path, seed, tag, n_games=None, workers=4):
    from appworld import AppWorld
    hooks = A.load_patch(patch_path) if patch_path not in (None, "none") else {}
    fp, pa, rp, mu, cf = (hooks.get(k) for k in ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback"))
    H = int(hooks.get("HISTORY_LENGTH", 20)); T = float(hooks.get("TEMPERATURE", 0.4)); tasks = TASKS[: (n_games or 10**9)]
    def play(i):
        bb = A.Backbone(T); tid = tasks[i]; state = {}; traj = []; steps = 0; success = False; gp = gf = 0; pre = REPLAY.get(tid) or []
        if HINTS.get(tid): state['_hint'] = HINTS[tid]
        with AppWorld(task_id=tid, experiment_name=f"line3_{tag}_s{seed}", random_seed=seed) as world:
            base = demo_messages(world.task.supervisor)
            # the demo ends with the example task; replace the last USER turn's task line with the real task
            task_msg = f"My name is: {world.task.supervisor.first_name} {world.task.supervisor.last_name}. My personal email is {world.task.supervisor.email} and phone number is {world.task.supervisor.phone_number}.\nTask: {world.task.instruction}"
            hist = []   # list of (assistant_text, user_output)
            for step in range(MAX_STEPS):
                A.GUARD.check()
                turns = hist[-H:]; msgs = base[:-1] + [{"role": "user", "content": base[-1]["content"].split("Task:")[0] + task_msg.split("\n")[-1] if False else task_msg}]
                for a_txt, u_out in turns: msgs += [{"role": "assistant", "content": a_txt}, {"role": "user", "content": u_out}]
                if step < len(pre):   # exact replay of a logged prefix: no LLM call, same code, environment is deterministic
                    code = pre[step]; out = world.execute(code); err = out.startswith("Execution failed")
                    try:
                        if mu: mu(state, hist[-1][1] if hist else "", code, out)
                    except Exception: pass
                    ev = world.evaluate().to_dict(); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail")
                    traj.append({"step": step, "code": code, "out": out[:200], "exec_error": int(err), "gp": gp, "gf": gf, "replayed": 1})
                    hist.append(("```python\n" + code + "\n```", "Output:\n```\n" + out[:3000] + "\n```")); steps += 1
                    if world.task_completed(): break
                    continue
                prompt0 = msgs[-1]["content"]; prompt = prompt0; si = {"pc": 0, "calls": 1}
                try:
                    if fp: prompt = fp(prompt, state)
                except Exception: pass
                si["pc"] = int(prompt != prompt0); msgs[-1] = {"role": "user", "content": prompt}
                resp = ""
                try:
                    r = bb.client.chat.completions.create(model=A.MODEL, messages=msgs, temperature=T, max_tokens=int(os.environ.get("BOS_MAX_TOKENS", "1024")), n=1, extra_body=bb.extra, **bb.sampling)
                    resp = (r.choices[0].message.content or ""); bb.tok[0] += r.usage.prompt_tokens; bb.tok[1] += r.usage.completion_tokens; bb.calls += 1
                except Exception as e:
                    bb.errors += 1; si["api_error"] = str(e)[:80]
                try: code = pa(resp, [], state) if pa else extract_code(resp)
                except Exception: code = extract_code(resp)
                si["parse_chg"] = int(bool(pa) and code != extract_code(resp)); si["a0"] = extract_code(resp)[:80]; si["a0_adm"] = int(bool(extract_code(resp)))
                attempt = 0
                while rp and not code and attempt < 2:
                    attempt += 1
                    try: pol = rp(attempt, resp, code, [], state)
                    except Exception: pol = None
                    if not pol: break
                    si["calls"] += 1
                    try:
                        r = bb.client.chat.completions.create(model=A.MODEL, messages=msgs + [{"role": "user", "content": pol.get("extra_instruction", "")}], temperature=pol.get("temperature", T), max_tokens=1024, n=1, extra_body=bb.extra, **bb.sampling)
                        resp = (r.choices[0].message.content or ""); bb.calls += 1
                    except Exception: pass
                    try: code = pa(resp, [], state) if pa else extract_code(resp)
                    except Exception: code = extract_code(resp)
                si["retry_n"] = attempt; si["retry_chg"] = int(attempt > 0 and bool(code)); si["fb"] = 0
                if not code and cf:
                    try: code = cf([], state) or ""; si["fb"] = int(bool(code))
                    except Exception: pass
                if not code: code = "print(apis.api_docs.show_app_descriptions())"; si["default_code"] = 1
                out = world.execute(code); err = out.startswith("Execution failed")
                try:
                    if mu: mu(state, hist[-1][1] if hist else "", code, out)
                except Exception: pass
                ev = world.evaluate().to_dict(); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail"); sf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_pass")
                traj.append({"step": step, "code": code, "resp": resp[-600:], "out": out[:200], "exec_error": int(err), "gp": gp, "gf": gf, "harm_fail": sf, **si})
                hist.append((resp if resp else "```python\n" + code + "\n```", "Output:\n```\n" + out[:3000] + "\n```")); steps += 1
                if world.task_completed(): break
            ev = world.evaluate().to_dict(); success = bool(ev.get("success")); gp = sum(1 for x in ev["passes"] if x.get("label") == "no_op_fail"); gf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_fail"); sf = sum(1 for x in ev["failures"] if x.get("label") == "no_op_pass")
        return i, {"bb": [bb.calls, bb.errors, bb.tok[0], bb.tok[1]], "task": tid, "won": success, "G": (gp / (gp + gf) if gp + gf else None), "harm_fail": sf, "steps": steps, "traj": traj}
    global _PLAY; _PLAY = play; results = [None] * len(tasks)
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context('fork')) as ex:
        for i, r in ex.map(_call, range(len(tasks))): results[i] = r
    class _B: pass
    bb = _B(); bb.calls = sum(r['bb'][0] for r in results); bb.errors = sum(r['bb'][1] for r in results); bb.tok = [sum(r['bb'][2] for r in results), sum(r['bb'][3] for r in results)]
    G = [r["G"] for r in results if r["G"] is not None]
    res = {"tag": tag, "patch": patch_path, "seed": seed, "model": A.MODEL, "history_length": H, "temperature": T, "n_games": len(tasks), "success_rate": sum(r["won"] for r in results) / len(tasks), "mean_G": sum(G) / max(len(G), 1),
           "won": [r["won"] for r in results], "G": [r["G"] for r in results], "harm_fail": [r["harm_fail"] for r in results], "games": [r["task"] for r in results], "steps": [r["steps"] for r in results], "traj": [r["traj"] for r in results],
           "calls": bb.calls, "api_errors": bb.errors, "tokens_in": bb.tok[0], "tokens_out": bb.tok[1], "finished": time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(f"{OUT}/results", exist_ok=True); json.dump(res, open(f"{OUT}/results/{tag}_seed{seed}.json", "w"))
    print(f"{tag} seed{seed}: success {res['success_rate']:.3f} mean_G {res['mean_G']:.2f} calls {bb.calls} api_errors {bb.errors}", flush=True)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--patch", default="none"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--tag", default="AW_F0"); ap.add_argument("--n-games", type=int, default=None); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(); run_eval(a.patch, a.seed, a.tag, a.n_games, a.workers)
