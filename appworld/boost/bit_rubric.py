"""BIT Unit C (docs/design/BIT_IMPLEMENTATION_PLAN.md): spec parser, spec -> v3 patch compiler, offline simulator.
A spec is {name, kind: note|block_once, cls, hypothesis, note, detect_src, origin}; detect(view) sees only the executed prefix
(Interface 1). compile_patch emits one edit eK per spec (Interface 3); simulate replays logged episodes through a patch with the
harness's hook-call rules, in a separate process with a wall timeout (a looping detector is rejected, not hung on).
usage: python boost/bit_rubric.py compile --spec a.json,b.json --out patch.py
       python boost/bit_rubric.py simulate (--spec a.json | --patch p.py) --runs A.json,B.json --instr instructions.json"""
import argparse, ast, json, multiprocessing as mp, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)

ALLOWED_IMPORTS = {"re", "json", "math", "random", "collections", "itertools", "string"}   # = common.ALLOWED_IMPORTS = bos_alfworld's
FORBIDDEN = {"open", "exec", "eval", "__import__", "compile", "globals", "locals", "getattr", "setattr", "delattr", "vars", "input",
             "breakpoint", "exit", "quit"}   # common.FORBIDDEN (a superset of bos_alfworld.FORBIDDEN)
POINTS = ("setup", "pre_call", "post_parse", "post_exec", "pre_complete")
KINDS = ("note", "block_once"); CLASSES = ("control_flow", "task_knowledge")


class SimulationError(RuntimeError): pass   # timeout / patch that cannot be loaded / worker crash


# ---------------------------------------------------------------- parse
_FIELD = r"^[ \t>#*_-]*{}[ \t*_]*:[ \t*_]*(.*)$"


def _field(sec, name, multiline=False):
    m = re.search(_FIELD.format(name), sec, re.M | re.I)
    if not m: return ""
    val = m.group(1).strip()
    if multiline:   # continuation lines until the next FIELD: line, a code fence or a blank line
        for line in sec[m.end():].split("\n")[1:]:
            if not line.strip() or line.strip().startswith("```") or re.match(r"^[ \t>#*_-]*[A-Z][A-Z_ ]{1,20}[ \t*_]*:", line): break
            val += " " + line.strip()
    return val.strip("*_ ").strip()


def _last_block(text):
    """last fenced python block; tolerates a final unclosed fence (same rule as proposer.last_block)."""
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", text, re.S)
    if text.count("```") % 2 == 1:
        tail = re.search(r"```(?:python|py)?[ \t]*\n((?:(?!```).)*)$", text, re.S)
        if tail: blocks.append(tail.group(1))
    return blocks[-1].strip("\n") + "\n" if blocks else None


def _split_block(src):
    """-> (NOTE string or None, source of the top-level def detect or the whole block if it does not parse)."""
    try: tree = ast.parse(src)
    except SyntaxError: return None, src
    note, det = None, None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NOTE" for t in n.targets) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            note = n.value.value
        if isinstance(n, ast.FunctionDef) and n.name == "detect": det = n
    if det is None: return note, src
    other = [n for n in tree.body if n is not det and not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NOTE" for t in n.targets))]
    if other: return note, src   # keep everything so validate_spec reports the stray statements
    lines = src.splitlines(); return note, "\n".join(lines[det.lineno - 1: det.end_lineno]) + "\n"


def parse_proposals(text):
    """proposer reply -> list of spec dicts (unvalidated). A candidate is the text from one 'NAME:' line to the next; fields KIND,
    CLASS, HYPOTHESIS; the section's last ```python block holds NOTE = "..." and def detect(view)."""
    text = text or ""; starts = [m.start() for m in re.finditer(_FIELD.format("NAME"), text, re.M | re.I)]; specs = []
    for a, b in zip(starts, starts[1:] + [len(text)]):
        sec = text[a:b]; block = _last_block(sec)
        if not block and "def detect(" in sec:   # lenient: code written without a ```python fence
            i = sec.find("NOTE =") if "NOTE =" in sec else sec.find("def detect("); block = sec[i:].strip().strip("`")
        name = re.sub(r"[^a-z0-9_]+", "_", _field(sec, "NAME").strip("`'\" ").lower()).strip("_")[:40]
        note, det = _split_block(block) if block else (None, "")
        specs.append({"name": name, "kind": _field(sec, "KIND").strip("`'\" ").lower(), "cls": _field(sec, "CLASS").strip("`'\" ").lower(),
                      "hypothesis": _field(sec, "HYPOTHESIS", multiline=True), "note": note or "", "detect_src": det,
                      "origin": {"case_id": None, "run": None}})
    return specs


# ---------------------------------------------------------------- validate
def _check_ast(tree, where):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name.split(".")[0] for x in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in ALLOWED_IMPORTS for n in names): raise ValueError(f"{where}: import not allowed: {names} (allowed: {sorted(ALLOWED_IMPORTS)})")
        if isinstance(node, ast.Name):
            if node.id in FORBIDDEN: raise ValueError(f"{where}: forbidden name {node.id}")
            if node.id.startswith("__"): raise ValueError(f"{where}: dunder name {node.id}")
            if node.id.startswith("_cc"): raise ValueError(f"{where}: names starting with _cc are reserved for the harness template")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"): raise ValueError(f"{where}: dunder attribute {node.attr}")
        if isinstance(node, (ast.Global, ast.Nonlocal)): raise ValueError(f"{where}: global/nonlocal not allowed")
        if isinstance(node, (ast.Yield, ast.YieldFrom, ast.Await)): raise ValueError(f"{where}: detect must be a plain function (no yield/await)")
        for nm in ([node.name] if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else []) + ([node.arg] if isinstance(node, ast.arg) else []):
            if nm.startswith("_cc") or nm.startswith("__"): raise ValueError(f"{where}: reserved name {nm}")
        if isinstance(node, (ast.Name, ast.FunctionDef, ast.arg)) and not (getattr(node, "id", None) or getattr(node, "name", None) or node.arg).isascii():
            raise ValueError(f"{where}: non-ASCII identifier")


def validate_spec(spec):
    """raises ValueError with a reason the proposer can act on; returns None if the spec compiles."""
    if not isinstance(spec, dict): raise ValueError("spec must be a dict")
    name = spec.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", name): raise ValueError(f"NAME must be snake_case, <= 40 chars: {name!r}")
    if spec.get("kind") not in KINDS: raise ValueError(f"KIND must be one of {KINDS}: {spec.get('kind')!r}")
    if spec.get("cls") not in CLASSES: raise ValueError(f"CLASS must be one of {CLASSES}: {spec.get('cls')!r}")
    if not isinstance(spec.get("hypothesis"), str) or not spec["hypothesis"].strip(): raise ValueError("HYPOTHESIS is missing")
    note = spec.get("note")
    if not isinstance(note, str) or not 20 <= len(note.strip()) <= 600: raise ValueError(f"NOTE must be a string literal of 20..600 chars (got {len(note.strip()) if isinstance(note, str) else type(note).__name__})")
    src = spec.get("detect_src")
    if not isinstance(src, str) or not src.strip(): raise ValueError("no python block with def detect(view)")
    try: tree = ast.parse(src)
    except SyntaxError as e: raise ValueError(f"detect block is not valid Python (SyntaxError: {e.msg}, line {e.lineno})")
    _check_ast(tree, "detect")
    dets = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "detect"]
    if len(dets) != 1: raise ValueError("the block must define exactly one top-level def detect(view)")
    a = dets[0].args
    if len(a.args) != 1 or a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs or dets[0].decorator_list:
        raise ValueError("detect must take exactly one argument: def detect(view)")
    for n in tree.body:
        if n is dets[0]: continue
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "NOTE": continue
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str): continue   # docstring
        raise ValueError(f"only NOTE = \"...\" and def detect(view) may appear at top level (line {n.lineno}); put imports and helpers inside detect")


# ---------------------------------------------------------------- compile
_HEAD = '''    if "_cc_task" not in _cc_state:
        _cc_state["_cc_task"] = _cc_prompt.split("Task:", 1)[1].strip() if _cc_state.get("_step") == 0 and "Task:" in _cc_prompt else ""
'''
_VIEW = '''    _cc_step = _cc_state.get("_step")
    if _cc_step is None:
        _cc_step = len(_cc_state.get("_cc_hist_{eid}", []))
'''
_RUN = '''    NOTE = {note}
{detect}    _cc_view = {{"task": _cc_state.get("_instr") or _cc_state.get("_cc_task") or "", "step": _cc_step, "max_steps": {max_steps},
                "cells": [dict(_cc_c) for _cc_c in _cc_state.get("_cc_hist_{eid}", [])], "pending": {pending}}}
    try:
        _cc_r = detect(_cc_view)
        _cc_fire = bool(_cc_r)
        _cc_note = (_cc_r if isinstance(_cc_r, str) and _cc_r.strip() else NOTE)[:600]
    except Exception:
        _cc_state["_cc_errors"] = _cc_state.get("_cc_errors", 0) + 1
        _cc_fire = False
'''
_NOTE_T = '''def {eid}_pre_call(_cc_prompt, _cc_state):
''' + _HEAD + '''    if _cc_state.get("_cc_done_{eid}"):
        return _cc_prompt
''' + _VIEW + '''    if _cc_state.get("_cc_noted") == _cc_step:
        return _cc_prompt
''' + _RUN + '''    if not _cc_fire:
        return _cc_prompt
    _cc_state["_cc_done_{eid}"] = True
    _cc_state["_cc_noted"] = _cc_step
    _cc_state.setdefault("_cc_fired", []).append({{"eid": "{eid}", "step": _cc_step, "kind": "note", "note": _cc_note}})
    return _cc_prompt + "\\n\\n[harness note] " + _cc_note
'''
_BLOCK_T = '''def {eid}_pre_call(_cc_prompt, _cc_state):
''' + _HEAD + '''    return _cc_prompt


def {eid}_post_parse(_cc_code, _cc_state):
    if _cc_state.get("_cc_done_{eid}"):
        return _cc_code
''' + _VIEW + '''    if _cc_step >= {max_steps} - 1 or _cc_state.get("_cc_blocked") == _cc_step:
        return _cc_code
''' + _RUN + '''    if not _cc_fire:
        return _cc_code
    _cc_state["_cc_done_{eid}"] = True
    _cc_state["_cc_blocked"] = _cc_step
    _cc_state.setdefault("_cc_fired", []).append({{"eid": "{eid}", "step": _cc_step, "kind": "block_once", "note": _cc_note, "pending": _cc_code[:300]}})
    return "print(" + repr("[harness note] Your cell was NOT executed. " + _cc_note) + ")"
'''
_EXEC_T = '''def {eid}_post_exec(_cc_code, _cc_out, _cc_state):
    _cc_out = _cc_out if isinstance(_cc_out, str) else str(_cc_out)
    _cc_state.setdefault("_cc_hist_{eid}", []).append({{"code": _cc_code or "", "out": _cc_out[:200], "error": _cc_out.startswith("Execution failed")}})
    return ""
'''


def _nested_detect(src):
    """the spec's def detect, canonicalised by ast.unparse (no comments; multi-line strings become escaped one-line literals, so
    re-indenting cannot change any string) and indented one level for nesting inside a hook."""
    det = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "detect"][0]
    return "".join("    " + l + "\n" for l in ast.unparse(det).splitlines())


def compile_patch(specs, max_steps=30):
    """specs (priority order) -> v3 patch source with edits e1..eN; validated by edits.structure_check before returning."""
    if not specs: raise ValueError("no specs")
    edits, funcs = [], []
    for j, sp in enumerate(specs, 1):
        validate_spec(sp); eid = f"e{j}"; det = _nested_detect(sp["detect_src"]); blk = sp["kind"] == "block_once"
        edits.append({"id": eid, "capability": "Verification", "impl": "ControlFlow" if blk else "Prompt", "trigger": sp["hypothesis"][:400],
                      "depends": [], "name": sp["name"], "kind": sp["kind"], "cls": sp["cls"], "origin": sp.get("origin")})
        t = _BLOCK_T if blk else _NOTE_T
        funcs.append(t.format(eid=eid, note=repr(sp["note"].strip()), detect=det, max_steps=int(max_steps), pending="_cc_code" if blk else "None"))
        funcs.append(_EXEC_T.format(eid=eid))
    src = (f'"""BIT patch compiled by boost/bit_rubric.py from {len(specs)} spec(s): {", ".join(s["name"] for s in specs)}."""\n\n'
           "EDITS = [\n" + "".join(f"    {e!r},\n" for e in edits) + "]\n\n\n" + "\n\n".join(funcs))
    asc = src.encode("ascii", "backslashreplace").decode("ascii")   # every literal is a non-raw repr, so \\uXXXX escapes keep their meaning
    if ast.dump(ast.parse(asc)) == ast.dump(ast.parse(src)): src = asc
    import edits as E   # lazy: edits imports numpy; simulate workers never need it
    E.structure_check(src)
    return src


# ---------------------------------------------------------------- simulate
def _load_patch(src):
    """same sandbox checks as bos_appworld_v3.load_v3 -> (edit ids in order, {point: [(eid, f)]})."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name.split(".")[0] for x in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in ALLOWED_IMPORTS for n in names): raise SimulationError(f"import not allowed: {names}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN: raise SimulationError(f"forbidden name {node.id}")
    ns = {}; exec(compile(src, "<patch>", "exec"), ns)
    ids = [e["id"] for e in (ns.get("EDITS") or [])]
    if not ids: raise SimulationError("not a v3 patch (EDITS missing or empty)")
    return ids, {p: [(e, ns[f"{e}_{p}"]) for e in ids if callable(ns.get(f"{e}_{p}"))] for p in POINTS}


class _Stub:
    """stand-in for the sandbox's `apis`: any attribute chain is callable and returns None."""
    def __getattr__(self, name): return _Stub()
    def __call__(self, *a, **k): return None


def _setup_ns(setup_srcs):
    """namespace with the patch's setup code (sandbox code normally run inside AppWorld) executed against a stub `apis`, or None if
    the setup code does not pass the patch sandbox rules / fails to run (then generic fires stay upper bounds)."""
    ns = {"apis": _Stub(), "_cc_printed": []}
    ns["print"] = lambda *a, **k: ns["_cc_printed"].append(" ".join(str(x) for x in a))
    try:
        for s in setup_srcs:
            _check_setup(ast.parse(s)); exec(compile(s, "<setup>", "exec"), ns)
    except Exception: return None
    return ns


def _check_setup(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [x.name.split(".")[0] for x in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            if any(n not in ALLOWED_IMPORTS for n in names): raise ValueError("setup import")
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN or node.id.startswith("__")): raise ValueError("setup name")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"): raise ValueError("setup dunder")


def _generic_code_fire(ns, before, after):
    """a hook rewrote the cell. If the rewrite only routes calls to setup-defined helpers and every argument of those calls is a literal,
    run the helpers on the stub and count a fire only if they print or raise (e.g. R3_H2 e1 sees answer=None and passes through).
    Otherwise (non-literal arguments, other rewrites, no usable setup) -> True: the upper bound."""
    if ns is None: return True
    try: tree = ast.parse(after); old = {n.id for n in ast.walk(ast.parse(before)) if isinstance(n, ast.Name)}
    except SyntaxError: return True
    helpers = {k for k, v in ns.items() if callable(v) and not k.startswith("__") and k not in ("print", "apis")} - old
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in helpers]
    if not calls: return True
    for c in calls:
        try:
            a = [ast.literal_eval(x) for x in c.args]; kw = {}
            for x in c.keywords:
                if x.arg is None: return True
                kw[x.arg] = ast.literal_eval(x.value)
        except Exception: return True   # a variable or expression argument: its run-time value is unknown offline
        n0 = len(ns["_cc_printed"])
        try: ns[c.func.id](*a, **kw)
        except Exception: return True
        if len(ns["_cc_printed"]) > n0: return True
    return False


def _prompt_proxy(ep, k, max_steps=30):
    """what the harness passes to pre_call: the task turn at step 0, afterwards the previous step's output turn (out <= 200 chars).
    Gaia2 (bos_gaia2.py): step 0 is "Current time: <dt>\nTask: <instr>" and the step counter uses the run's max_steps."""
    g2 = ep.get("bench") == "gaia2"
    if k == 0:
        if g2: return f"Current time: (t)\nTask: {ep.get('instr', '')}"
        return f"My name is: (user). My personal email is (email) and phone number is (phone).\nTask: {ep.get('instr', '')}"
    if g2: max_steps = ep.get("max_steps") or max_steps
    prev = ep["steps"][k - 1]
    return "Output:\n```\n" + prev["out"] + "\n```" + (f"\n[{k} of {max_steps} steps used]" if ep.get("harness_h1", True) else "")


def _simulate(src, eps, stop_at_first=True):
    ids, F = _load_patch(src); template = "_cc_fired" in src; res = {}
    for ep in eps:
        state = {"_instr": ep.get("instr", "")}; fires, errs, stopped = [], 0, set()
        marker = "send_message_to_user" if ep.get("bench") == "gaia2" else "complete_task"   # the harness's pre_complete trigger
        n_rep = sum(1 for s in ep["steps"] if s.get("replayed"))

        def call(eid, point, f, *args):
            nonlocal errs
            n0 = len(state.get("_cc_fired", []))
            try: r = f(*args)
            except Exception: errs += 1; return None, []
            return r, state.get("_cc_fired", [])[n0:]

        def record(eid, k, new, generic=None):
            for x in new:
                fires.append({"eid": x.get("eid", eid), "edit": x.get("eid", eid), "k": k, "kind": x.get("kind"), "note": x.get("note"), "pending": x.get("pending")})
            if generic is not None: fires.append({"eid": eid, "edit": eid, "k": k, "kind": "generic", **generic})
            if (new or generic is not None) and stop_at_first: stopped.add(eid)

        setup_srcs = []
        for eid, f in F["setup"]:
            try: sc = f(); setup_srcs += [sc] if isinstance(sc, str) and sc.strip() else []
            except Exception: errs += 1
        ns = None if template else _setup_ns(setup_srcs)
        for i, s in enumerate(ep["steps"]):
            k = s.get("k", i)
            if s.get("replayed"):
                for eid, f in F["post_exec"]:
                    if eid not in stopped: call(eid, "post_exec", f, s["code"], s["out"], state)
                continue
            state["_step"], state["_tid"], state["_replay_len"] = k, ep.get("task"), n_rep
            prompt = _prompt_proxy(ep, i)
            for eid, f in F["pre_call"]:
                if eid in stopped: continue
                r, new = call(eid, "pre_call", f, prompt, state); p2 = r if isinstance(r, str) and r.strip() else prompt
                gen = None if template or p2 == prompt else {"note": (p2[len(prompt):] if p2.startswith(prompt) else p2)[:600], "pending": None}
                record(eid, k, new, gen); prompt = p2
            if s.get("no_exec") or not s["code"]: continue
            code = s["code"]
            for point in ("post_parse", "pre_complete"):
                if point == "pre_complete" and marker not in code: break
                for eid, f in F[point]:
                    if eid in stopped: continue
                    r, new = call(eid, point, f, code, state); c2 = r if isinstance(r, str) and r.strip() else code
                    gen = None if template or c2 == code or not _generic_code_fire(ns, code, c2) else {"note": c2[:600], "pending": code[:300]}
                    record(eid, k, new, gen); code = c2
            for eid, f in F["post_exec"]:
                if eid not in stopped: call(eid, "post_exec", f, s["code"], s["out"], state)
        res[ep["eid"]] = {"fires": fires, "hook_errors": errs + int(state.get("_cc_errors", 0) or 0)}
    return res


def _worker(conn, src, eps, stop_at_first):
    try: conn.send(("ok", _simulate(src, eps, stop_at_first)))
    except BaseException as e: conn.send(("err", f"{type(e).__name__}: {str(e)[:300]}"))
    finally: conn.close()


def simulate(patch_src, eps, stop_at_first=True, timeout_s=120):
    """-> {episode eid: {"fires": [{"eid": edit id, "edit", "k", "kind", "note", "pending"}], "hook_errors": int}}.
    Runs in a spawned process (Windows has no SIGALRM; fork is unsafe in threaded callers); raises SimulationError on timeout,
    an unloadable patch or a worker crash. timeout_s=None runs in-process (no protection against looping detectors)."""
    if timeout_s is None:
        try: return _simulate(patch_src, eps, stop_at_first)
        except SimulationError: raise
        except Exception as e: raise SimulationError(f"{type(e).__name__}: {str(e)[:300]}")
    ctx = mp.get_context("spawn"); rx, tx = ctx.Pipe(duplex=False)
    p = ctx.Process(target=_worker, args=(tx, patch_src, eps, stop_at_first), daemon=True); p.start(); tx.close()
    try:
        if not rx.poll(timeout_s):
            raise SimulationError(f"simulation timed out after {timeout_s}s (a detector probably loops)")
        try: status, val = rx.recv()
        except EOFError: raise SimulationError(f"simulation worker died (exit code {p.exitcode})")
    finally:
        if p.is_alive(): p.terminate()
        p.join(5); rx.close()
    if status != "ok": raise SimulationError(val)
    return val


# ---------------------------------------------------------------- episodes + CLI
def load_episodes(paths, instr):
    try:
        import bit_common
        return bit_common.load_episodes(paths, instr)
    except ImportError:
        return _load_episodes(paths, instr)


def _load_episodes(paths, instr):
    """minimal fallback with the same fields as bit_common.load_episodes (used only if Unit A's module is absent)."""
    if isinstance(paths, str): paths = [p for p in paths.split(",") if p]
    if isinstance(instr, str): instr = json.load(open(instr, encoding="utf-8"))
    eps = []
    for p in paths:
        d = json.load(open(p, encoding="utf-8")); n = len(d["games"]); crashed = d.get("crashed") or [None] * n; Gs = d.get("G") or [None] * n
        for t, w, tr, cr, G in zip(d["games"], d["won"], d["traj"], crashed, Gs):
            steps = []
            for s in tr or []:
                code = s.get("code") or ""; out = s.get("out") or ""; rep = bool(s.get("replayed"))
                steps.append({"k": s["step"], "code": code, "out": out, "err": out.startswith("Execution failed"),
                              "no_exec": bool(s.get("no_exec")) or (not code and not rep), "replayed": rep, "resp": s.get("resp") or ""})
            eps.append({"eid": f"{d['tag']}_s{d['seed']}:{t}", "task": t, "tag": d["tag"], "seed": d["seed"], "won": bool(w), "G": G,
                        "instr": instr.get(t, ""), "harness_h1": bool(d.get("harness_h1")), "crashed": bool(cr),
                        "has_replay": any(s["replayed"] for s in steps), "bench": d.get("bench", "appworld"), "max_steps": d.get("max_steps"),
                        "steps": steps})
    return eps


def summarize(res, eps):
    """per edit: fired losses / fired wins (first fire per episode)."""
    byid = {e["eid"]: e for e in eps}; out = {}
    for eid, r in res.items():
        for ed in sorted({f["eid"] for f in r["fires"]}):
            o = out.setdefault(ed, {"loss": [], "win": []}); o["win" if byid[eid]["won"] else "loss"].append(eid)
    n_l = sum(1 for e in eps if not e["won"]); n_w = len(eps) - n_l
    return {ed: {"losses": f"{len(o['loss'])}/{n_l}", "wins": f"{len(o['win'])}/{n_w}", "fired_losses": o["loss"], "fired_wins": o["win"]} for ed, o in out.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["compile", "simulate"]); ap.add_argument("--spec"); ap.add_argument("--patch")
    ap.add_argument("--out"); ap.add_argument("--runs"); ap.add_argument("--instr"); ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=120); a = ap.parse_args()
    if a.spec: src = compile_patch([json.load(open(p, encoding="utf-8")) for p in a.spec.split(",")], a.max_steps)
    else: src = open(a.patch, encoding="utf-8").read()
    if a.cmd == "compile":
        if a.out: open(a.out, "w", encoding="utf-8").write(src)
        else: print(src)
        return
    eps = [e for e in load_episodes(a.runs, a.instr) if not e["crashed"]]; res = simulate(src, eps, timeout_s=a.timeout)
    print(json.dumps({"n": len(eps), "hook_errors": sum(r["hook_errors"] for r in res.values()), "edits": summarize(res, eps)}, indent=1))


if __name__ == "__main__":
    main()
