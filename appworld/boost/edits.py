"""CC-BOOST Stage 2: rubric-guided harness edits (prereg section 2). Same self-proposer, same template; only the GUIDANCE block differs:
  G_BOOST    a top boosted rubric dimension (by failure mass) + its detector + 3 failures where it fires; edit must trigger on it online
  G_RAW      3 random failures, "find a mechanism and repair it"
  G_GENERIC  generic rubric text (tool-call accuracy / avoid loops / explore alternatives) + 3 random failures
Each patch must load (load_v3) and fire on >= MIN_FIRE discovery tasks in an offline dry-run, else it is regenerated (<= 3 tries).
usage: python boost/edits.py --arm G_BOOST --boost-state boost/out/run1/BOOST/state.json --disc results/X_seed1.json,... --k 3 --tag CC_BE1"""
import argparse, json, os, random, re, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AW = os.path.dirname(HERE); sys.path.insert(0, HERE); sys.path.insert(0, AW)
import common as C, proposer as PR

MIN_FIRE = int(os.environ.get("BOOST_MIN_FIRE", "3"))
IFACE = open(os.path.join(AW, "bos_appworld_v3.py")).read().split('"""')[1]
SPACE = ("SEARCH SPACE: an edit is a capability (Planning, Memory, ToolUse, Recovery, Verification) x implementation (Prompt, State, Code, "
         "ControlFlow) attached to a control point. State = the harness maintains/injects structured state; Code = the harness rewrites or "
         "post-processes the model's code; ControlFlow = the harness changes what executes when (e.g. block a premature complete_task once). "
         "Prompt = a targeted message injected into the prompt; use it only when the edit fires on a specific condition, never as an always-on instruction.")
FORMAT = ("OUTPUT FORMAT: a line 'NAME: <snake_case>', then ONE python code block with a complete v3 patch module: EDITS = [{\"id\": \"e1\", "
          "\"capability\": ..., \"impl\": ..., \"trigger\": <when it fires>, \"depends\": [], \"expected_effect\": ..., \"side_effect_risk\": ...}, ...] and functions "
          "<id>_setup() -> str | <id>_pre_call(prompt, state) -> str | <id>_post_parse(code, state) -> str | <id>_post_exec(code, out, state) -> None | "
          "<id>_pre_complete(code, state) -> str. Allowed imports: re, json, math, random, collections, itertools, string (import inside functions). "
          "No file or network access. Use 1-3 edits: the minimal executable repair. Every edit must fire only under its stated trigger.")
GENERIC = ("GENERIC GUIDANCE (a fixed rubric of good agent behaviour): (1) make accurate tool calls (correct API names and arguments, read the docs "
           "when unsure); (2) do not get stuck in loops (repeating the same failing call or inspection); (3) explore alternative approaches when the "
           "current one is not working.")


def failure_mass(state, rd):
    """contribution c_ik = w_k * z_ik of each admitted dimension on discovery landmark failures; mass_k = sum_i max(0, -c_ik)."""
    rub = state["rubric"]; fns = [C.compile_detector(d["src"]) for d in rub]
    F = np.array([C.run_detector(f, rd)[0] for f in fns]).T; Z, _ = C.standardize(F); y = np.array([r["y"] for r in rd], float)
    w = C.fit_logit(Z, y); c = Z * w[1:]; fail = y == 0
    mass = np.maximum(0, -c[fail]).sum(0)
    return [{"k": k, "name": rub[k]["name"], "desc": rub[k]["desc"], "src": rub[k]["src"], "w": float(w[1 + k]), "mass": float(mass[k]),
             "top_fail": [int(i) for i in np.nonzero(fail)[0][np.argsort(c[fail][:, k])[:3]]]} for k in np.argsort(-mass)]


def guidance(arm, j, rd, instr, dims, rng):
    fails = [i for i, r in enumerate(rd) if r["y"] == 0]
    def win(i): return f"TASK: {instr.get(rd[i]['task'], '(instruction unavailable)')[:400]}\nFIRST CELLS:\n{C.window(rd[i]['cells'])}"
    if arm == "G_BOOST":
        d = dims[j % len(dims)]; ex = "\n\n".join(f"--- failed trajectory {n + 1} ---\n{win(i)}" for n, i in enumerate(d["top_fail"]))
        if d["w"] < 0: how, where = f"HIGH values predict failure (weight {d['w']:+.2f} on success)", "where the detector value is high"
        else: how, where = f"LOW values predict failure, i.e. failing runs tend NOT to show this behaviour (weight {d['w']:+.2f} on success)", "where the detector value is low (the behaviour is missing)"
        return (f"RUBRIC FINDING (from an executable rubric learned on this agent's own trajectories): dimension `{d['name']}`: {d['desc']}\n"
                f"{how}; it accounts for the largest share of failures not explained by the other dimensions. Its detector, computed on the agent's "
                f"first {C.L} cells (each cell: 'code', 'out' = first 200 chars of output, 'error', 'reply'):\n```python\n{d['src']}```\n"
                f"Three failed trajectories {where}:\n{ex}\n\nWrite a harness patch whose trigger is THIS condition detected ONLINE: record the "
                f"executed cells in `state` (post_exec), evaluate the failure-side condition, and intervene (pre_call / post_parse / pre_complete) only when it holds."), d["name"]
    pick = rng.sample(fails, 3); ex = "\n\n".join(f"--- failed trajectory {n + 1} ---\n{win(i)}" for n, i in enumerate(pick))
    if arm == "G_RAW": return f"Three failed trajectories of the current agent:\n{ex}\n\nFind a concrete failure mechanism and write the minimal harness patch that repairs it.", None
    return f"{GENERIC}\n\nThree failed trajectories of the current agent:\n{ex}\n\nWrite a harness patch that improves the agent along these lines.", None


def dry_run(path, trajs, instr):
    """offline firing count on logged trajectories: does any hook change the prompt, the code, or the state?"""
    import bos_appworld_v3 as V
    active, off, funcs, legacy, consts = V.load_v3(path); fire_tasks = fire_steps = errs = 0
    for task, tr in trajs:
        state = {}; fired_task = False
        for f in [f for _, f in funcs["setup"]]:
            try: f()
            except Exception: errs += 1
        for t, s in enumerate(tr):
            prompt = f"Task: {instr.get(task, '')}" if t == 0 else "Output:\n```\n" + tr[t - 1]["out"] + "\n```"; code = s["code"]; fired = False
            for _, f in funcs["pre_call"]:
                try: p2 = f(prompt, state); fired |= isinstance(p2, str) and p2 != prompt
                except Exception: errs += 1
            for _, f in funcs["post_parse"]:
                try: c2 = f(code, state); ch = isinstance(c2, str) and c2.strip() and c2 != code; fired |= bool(ch); code = c2 if ch else code
                except Exception: errs += 1
            if "complete_task" in code:
                for _, f in funcs["pre_complete"]:
                    try: c2 = f(code, state); fired |= bool(isinstance(c2, str) and c2.strip() and c2 != code)
                    except Exception: errs += 1
            for _, f in funcs["post_exec"]:
                try: f(s["code"], s["out"], state)
                except Exception: errs += 1
            fire_steps += int(fired); fired_task |= fired
        fire_tasks += int(fired_task)
    return {"fire_tasks": fire_tasks, "fire_steps": fire_steps, "errors": errs, "n_tasks": len(trajs), "edits": [e["id"] for e in active]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=["G_BOOST", "G_RAW", "G_GENERIC"]); ap.add_argument("--boost-state")
    ap.add_argument("--disc", required=True); ap.add_argument("--k", type=int, default=3); ap.add_argument("--tag", required=True); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--instr", default=None); a = ap.parse_args()
    pd = os.path.join(AW, "patches_ccboost"); os.makedirs(pd, exist_ok=True)
    allrecs = C.load_runs(a.disc.split(",")); rd = [r for r in allrecs if r["at_risk"]]
    instr = json.load(open(a.instr)) if a.instr and os.path.exists(a.instr) else {}
    trajs = []
    for p in a.disc.split(","):
        d = json.load(open(p)); trajs += [(t, tr) for t, tr in zip(d["games"], d["traj"])]
    dims = failure_mass(json.load(open(a.boost_state)), rd) if a.arm == "G_BOOST" else None
    if dims is not None:
        dims = [d for d in dims if d["mass"] > 0][:3]   # top-3 by failure mass, either orientation (presence or absence predicts failure)
        print("failure mass (top):", [(d["name"], round(d["mass"], 2), round(d["w"], 2)) for d in dims], flush=True)
        if not dims: sys.exit("G_BOOST: the boosted rubric has no dimension with failure mass; nothing to target")
    rng = random.Random(1000 + a.seed); meta = []
    for j in range(a.k):
        g, target = guidance(a.arm, j, rd, instr, dims, rng)
        user = f"{IFACE}\n\n{SPACE}\n\nPARENT HARNESS: bare (no edits).\n\n{g}\n\n{FORMAT}"
        msgs = [{"role": "system", "content": "You are a careful engineer improving an LLM agent harness through small, executable, well-triggered edits."}, {"role": "user", "content": user}]
        rec = {"arm": a.arm, "j": j, "target": target, "attempts": []}
        for att in range(3):
            text, use = PR.chat(msgs); src = PR.last_block(text, "EDITS"); nm = PR.field(text, "NAME") or "cand"
            pid = f"{a.tag}_{a.arm}_{j}_{re.sub(r'[^A-Za-z0-9_]', '', nm)[:24]}"; path = os.path.join(pd, pid + ".py")
            try:
                if not src: raise ValueError("no python block with EDITS")
                src = "\n".join(l for l in src.splitlines() if not re.match(r"\s*(NAME|TARGET)\s*:", l)) + "\n"; open(path, "w").write(src)
                dr = dry_run(path, trajs, instr)
                if dr["fire_tasks"] < MIN_FIRE: raise ValueError(f"dead or near-dead edit: fires on {dr['fire_tasks']} of {dr['n_tasks']} logged discovery tasks (need >= {MIN_FIRE})")
                rec.update(pid=pid, path=path, dry_run=dr, valid=True); rec["attempts"].append({"usage": use, "ok": True}); break
            except Exception as e:
                why = f"{type(e).__name__}: {str(e)[:200]}"; rec["attempts"].append({"usage": use, "ok": False, "why": why})
                msgs += [{"role": "assistant", "content": text[-6000:]}, {"role": "user", "content": f"Your patch failed validation: {why}. Fix it and output again."}]
        rec.setdefault("valid", False); meta.append(rec); print(json.dumps({k: rec.get(k) for k in ("arm", "j", "target", "pid", "valid", "dry_run")}), flush=True)
    json.dump(meta, open(os.path.join(pd, f"{a.tag}_{a.arm}_meta.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
