"""CC-BOOST Stage 2: rubric-guided harness edits (prereg section 2). Same self-proposer, same template; only the GUIDANCE block differs:
  G_BOOST    a top boosted rubric dimension (by failure mass) + its detector + 3 failures on its failure side; edit must trigger on it
  G_RAW      3 random failures, "find a mechanism and repair it"
  G_GENERIC  generic rubric text (tool-call accuracy / avoid loops / explore alternatives) + 3 random failures
Each patch must pass a structure check and an offline dry-run (no None prompts, no raising setup, fires on >= MIN_FIRE distinct
discovery tasks), else it is regenerated (<= 3 tries).
usage: python boost/edits.py --arm G_BOOST --boost-state OUT/BOOST/state.json --disc R1.json,R2.json --instr OUT/instructions.json --k 3 --tag CC_BE1"""
import argparse, ast, json, os, random, re, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AW = os.path.dirname(HERE); sys.path.insert(0, HERE); sys.path.insert(0, AW)
import common as C, proposer as PR

MIN_FIRE = int(os.environ.get("BOOST_MIN_FIRE", "3"))
POINTS = ("setup", "pre_call", "post_parse", "post_exec", "pre_complete")
LEGACY = ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback", "HISTORY_LENGTH", "TEMPERATURE", "SETUP_CODE")
IFACE = open(os.path.join(AW, "bos_appworld_v3.py")).read().split('"""')[1]
SPACE = ("SEARCH SPACE: an edit is a capability (Planning, Memory, ToolUse, Recovery, Verification) x implementation (Prompt, State, Code, "
         "ControlFlow) attached to a control point. State = the harness maintains/injects structured state; Code = the harness rewrites or "
         "post-processes the model's code; ControlFlow = the harness changes what executes when (e.g. block a premature complete_task once). "
         "Prompt = a targeted message injected into the prompt; use it only when the edit fires on a specific condition, never as an always-on instruction.")
FORMAT = ("OUTPUT FORMAT: a line 'NAME: <snake_case>', then ONE python code block with a complete v3 patch module: EDITS = [{\"id\": \"e1\", "
          "\"capability\": ..., \"impl\": ..., \"trigger\": <when it fires>, \"depends\": [], \"expected_effect\": ..., \"side_effect_risk\": ...}, ...] and functions "
          "<id>_setup() -> str | <id>_pre_call(prompt, state) -> str | <id>_post_parse(code, state) -> str | <id>_post_exec(code, out, state) -> None | "
          "<id>_pre_complete(code, state) -> str.\nRULES: edit ids are e1, e2, e3 (no underscores). The ONLY top-level functions allowed are "
          "<id>_<point> for those ids; put helpers inside the hook functions. Do not define the legacy hooks (format_prompt, parse_action, retry_policy, "
          "memory_update, choose_fallback) or HISTORY_LENGTH / TEMPERATURE / SETUP_CODE. pre_call / post_parse / pre_complete must ALWAYS return a "
          "string: the unchanged prompt or code when the edit does not fire. To fire on a condition, record what you need about executed cells in "
          "`state` in post_exec, test the condition, and intervene in pre_call / post_parse / pre_complete only when it holds. Allowed imports: re, "
          "json, math, random, collections, itertools, string (import inside functions). No file or network access. Use 1-3 edits: the minimal "
          "executable repair. Every edit must fire only under its stated trigger.")
GENERIC = ("GENERIC GUIDANCE (a fixed rubric of good agent behaviour): (1) make accurate tool calls (correct API names and arguments, read the docs "
           "when unsure); (2) do not get stuck in loops (repeating the same failing call or inspection); (3) explore alternative approaches when the "
           "current one is not working.")


def failure_mass(state, rd):
    """contribution c_ik = w_k * z_ik of each admitted dimension on discovery landmark failures; mass_k = sum_i max(0, -c_ik).
    top_fail = up to 3 failures (distinct tasks) where dimension k pushes hardest toward failure."""
    rub = state["rubric"]
    if not rub: return []
    fns = [C.compile_detector(d["src"]) for d in rub]
    F = np.array([C.run_detector(f, rd)[0] for f in fns]).T; Z, _ = C.standardize(F); y = np.array([r["y"] for r in rd], float)
    w = C.fit_logit(Z, y); c = Z * w[1:]; fail_idx = np.nonzero(y == 0)[0]; mass = np.maximum(0, -c[fail_idx]).sum(0); out = []
    for k in np.argsort(-mass):
        top, seen = [], set()
        for i in fail_idx[np.argsort(c[fail_idx, k])]:
            if rd[i]["task"] in seen: continue
            top.append(int(i)); seen.add(rd[i]["task"])
            if len(top) == 3: break
        out.append({"k": int(k), "name": rub[k]["name"], "desc": rub[k]["desc"], "src": rub[k]["src"], "w": float(w[1 + k]), "mass": float(mass[k]), "top_fail": top})
    return out


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
                f"Three failed trajectories {where}:\n{ex}\n\nWrite a harness patch whose trigger is THIS condition (its failure side), detected online."), d["name"]
    pick, seen = [], set()
    for i in rng.sample(fails, len(fails)):
        if rd[i]["task"] in seen: continue
        pick.append(i); seen.add(rd[i]["task"])
        if len(pick) == 3: break
    ex = "\n\n".join(f"--- failed trajectory {n + 1} ---\n{win(i)}" for n, i in enumerate(pick))
    if arm == "G_RAW": return f"Three failed trajectories of the current agent:\n{ex}\n\nFind a concrete failure mechanism and write the minimal harness patch that repairs it.", None
    return f"{GENERIC}\n\nThree failed trajectories of the current agent:\n{ex}\n\nWrite a harness patch that improves the agent along these lines.", None


def structure_check(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):   # same sandbox rules as load_v3, checked BEFORE executing anything
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name.split(".")[0] for x in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in C.ALLOWED_IMPORTS for n in names): raise ValueError(f"import not allowed: {names}")
        if isinstance(node, ast.Name) and node.id in C.FORBIDDEN: raise ValueError(f"forbidden name {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"): raise ValueError("dunder attribute")
    ns = {}; exec(compile(src, "<patch>", "exec"), ns)
    ids = [e.get("id") for e in (ns.get("EDITS") or [])]
    if not ids: raise ValueError("EDITS is empty or missing")
    bad_ids = [i for i in ids if not isinstance(i, str) or "_" in i or not i]
    if bad_ids: raise ValueError(f"edit ids must be like e1, e2 (no underscores): {bad_ids}")
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            eid, _, pt = n.name.partition("_")
            if eid not in ids or pt not in POINTS: raise ValueError(f"top-level function {n.name} is not <id>_<point> for an id in EDITS; move helpers inside a hook")
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                if isinstance(t, ast.Name) and t.id in LEGACY: raise ValueError(f"{t.id} is not allowed in a v3 patch here")
    legacy = [h for h in LEGACY if h in ns and callable(ns[h])]
    if legacy: raise ValueError(f"legacy hooks not allowed: {legacy}")


def dry_run(V, path, trajs, instr):
    """offline replay of logged trajectories through the patch, mirroring bos_appworld_v3's hook calls. Raises on harness-breaking behaviour."""
    active, off, funcs, legacy, consts = V.load_v3(path); fire_tasks, fire_steps, errs, steps = set(), 0, 0, 0
    for task, tr in trajs:
        state = {}
        for eid, f in funcs["setup"]:
            sc = f()
            if not isinstance(sc, str): raise ValueError(f"{eid}_setup must return a code string, got {type(sc).__name__}")
            compile(sc, "<setup>", "exec")
        for t, s in enumerate(tr):
            steps += 1
            prompt0 = f"My name is: (user).\nTask: {instr.get(task, '')}" if t == 0 else "Output:\n```\n" + tr[t - 1]["out"] + "\n```"; prompt = prompt0; code = s["code"]; fired = False
            for eid, f in funcs["pre_call"]:
                try: p2 = f(prompt, state)
                except Exception: errs += 1; continue
                if not isinstance(p2, str) or not p2.strip(): raise ValueError(f"{eid}_pre_call returned {type(p2).__name__} (must return the prompt string, unchanged when not firing)")
                prompt = p2
            fired |= prompt != prompt0
            for eid, f in funcs["post_parse"]:
                try: c2 = f(code, state); code2 = c2 if isinstance(c2, str) and c2.strip() else code; fired |= code2 != code; code = code2
                except Exception: errs += 1
            if "complete_task" in code:
                for eid, f in funcs["pre_complete"]:
                    try: c2 = f(code, state); code2 = c2 if isinstance(c2, str) and c2.strip() else code; fired |= code2 != code; code = code2
                    except Exception: errs += 1
            for eid, f in funcs["post_exec"]:
                try: f(s["code"], s["out"], state)
                except Exception: errs += 1
            fire_steps += int(fired)
            if fired: fire_tasks.add(task)
    if errs > 0.2 * steps: raise ValueError(f"hooks raised on {errs} of {steps} replayed steps")
    return {"fire_tasks": len(fire_tasks), "fire_steps": fire_steps, "hook_errors": errs, "steps": steps, "n_tasks": len({t for t, _ in trajs}), "edits": [e["id"] for e in active]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=["G_BOOST", "G_RAW", "G_GENERIC"]); ap.add_argument("--boost-state")
    ap.add_argument("--disc", required=True); ap.add_argument("--k", type=int, default=3); ap.add_argument("--tag", required=True); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--instr", required=True); a = ap.parse_args()
    import bos_appworld_v3 as V   # environment problems surface here, not as "patch failures" fed back to the proposer
    pd = os.path.join(AW, "patches_ccboost"); os.makedirs(pd, exist_ok=True)
    rd = [r for r in C.load_runs(a.disc.split(",")) if r["at_risk"]]; instr = json.load(open(a.instr))
    missing = [t for t in {r["task"] for r in rd} if t not in instr]
    if missing: sys.exit(f"instructions missing for {len(missing)} discovery tasks")
    trajs = []
    for p in a.disc.split(","):
        d = json.load(open(p)); trajs += [(t, tr) for t, tr in zip(d["games"], d["traj"])]
    dims = None
    if a.arm == "G_BOOST":
        st = json.load(open(a.boost_state))
        if st.get("L") != C.L: sys.exit(f"landmark mismatch: state L={st.get('L')} vs BOOST_L={C.L}")
        dims = [d for d in failure_mass(st, rd) if d["mass"] > 0][:3]   # top-3 by failure mass, either orientation
        print("failure mass (top):", [(d["name"], round(d["mass"], 2), round(d["w"], 2)) for d in dims], flush=True)
        if not dims: sys.exit("G_BOOST: the boosted rubric has no dimension with failure mass; nothing to target")
    rng = random.Random(1000 + a.seed); meta, mpath = [], os.path.join(pd, f"{a.tag}_{a.arm}_meta.json")
    for j in range(a.k):
        g, target = guidance(a.arm, j, rd, instr, dims, rng)
        user = f"{IFACE}\n\n{SPACE}\n\nPARENT HARNESS: bare (no edits).\n\n{g}\n\n{FORMAT}"
        msgs = [{"role": "system", "content": "You are a careful engineer improving an LLM agent harness through small, executable, well-triggered edits."}, {"role": "user", "content": user}]
        rec = {"arm": a.arm, "j": j, "target": target, "attempts": []}
        for att in range(3):
            text, use = PR.safe_chat(msgs); src = PR.last_block(text, "EDITS"); nm = PR.field(text, "NAME") or "cand"
            pid = f"{a.tag}_{a.arm}_{j}_{re.sub(r'[^A-Za-z0-9_]', '', nm)[:24]}"; path = os.path.join(pd, pid + ".py")
            try:
                if not src: raise ValueError(f"no python block with EDITS (finish={use.get('finish')})")
                src = "\n".join(l for l in src.splitlines() if not re.match(r"\s*(NAME|TARGET)\s*:", l)) + "\n"
                structure_check(src); open(path, "w").write(src)
                dr = dry_run(V, path, trajs, instr)
                if dr["fire_tasks"] < MIN_FIRE: raise ValueError(f"dead or near-dead edit: fires on {dr['fire_tasks']} of {dr['n_tasks']} logged discovery tasks (need >= {MIN_FIRE})")
                rec.update(pid=pid, path=path, dry_run=dr, valid=True); rec["attempts"].append({"usage": use, "ok": True}); break
            except Exception as e:
                why = f"{type(e).__name__}: {str(e)[:200]}"; rec["attempts"].append({"usage": use, "ok": False, "why": why})
                if os.path.exists(path) and not rec.get("valid"): os.remove(path)
                msgs += [{"role": "assistant", "content": text[-6000:]}, {"role": "user", "content": f"Your patch failed validation: {why}. Fix it and output again."}]
        rec.setdefault("valid", False); meta.append(rec); json.dump(meta, open(mpath, "w"), indent=1)
        print(json.dumps({k: rec.get(k) for k in ("arm", "j", "target", "pid", "valid", "dry_run")}), flush=True)


if __name__ == "__main__":
    main()
