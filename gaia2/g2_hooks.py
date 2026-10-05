"""Gaia2 harness patch loading (docs/design/GAIA2_ADAPTER_PLAN.md, U4). A copy of bos_appworld_v3.load_v3 with the sandbox constants of
alfworld/bos_alfworld.py, so that bos_gaia2 never imports the AppWorld harness (it reads BOS_TASKS / its instructions file at import
time and cannot be imported in are-env). A v3 patch is a module with EDITS = [{id, ...}] and functions <id>_setup() -> sandbox code |
<id>_pre_call(prompt, state) -> prompt | <id>_post_parse(code, state) -> code | <id>_post_exec(code, out, state) -> None |
<id>_pre_complete(code, state) -> code (Gaia2: only when the cell calls send_message_to_user). BOS_EDITS_OFF="e2,e4" disables edits
(dependency-closed). Also the point runners used by bos_gaia2 (same exception / None-return rules as bos_appworld_v3)."""
import ast as _ast, os

ALLOWED_IMPORTS = {"re", "json", "math", "random", "collections", "itertools", "string"}   # = bos_alfworld.ALLOWED_IMPORTS
FORBIDDEN = {"open", "exec", "eval", "__import__", "compile", "globals", "locals", "getattr", "setattr", "input", "breakpoint"}   # = bos_alfworld.FORBIDDEN
HOOKS = ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback")   # = bos_alfworld.HOOKS (legacy names, tolerated by the validator)
ALLOWED_POINTS = ("setup", "pre_call", "post_parse", "post_exec", "pre_complete")
PRE_COMPLETE_MARKER = "send_message_to_user"   # Gaia2's turn-ending call (AppWorld: complete_task)


def load_v3(path):
    """validate + load a two-layer patch; returns (active edits, off ids, funcs_by_point, legacy hooks, consts) with OFF edits
    (dependency-closed) removed. Same semantics as bos_appworld_v3.load_v3."""
    src = open(path, encoding="utf-8").read(); tree = _ast.parse(src)
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Import, _ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, _ast.Import) else [(node.module or "").split(".")[0]]
            assert all(n in ALLOWED_IMPORTS for n in names), f"import not allowed: {names}"
        if isinstance(node, _ast.Name) and node.id in FORBIDDEN: raise AssertionError(f"forbidden name {node.id}")
    ns = {}; exec(compile(src, path, "exec"), ns)
    edits = ns.get("EDITS") or []
    ids = [e["id"] for e in edits]; assert len(ids) == len(set(ids)), "duplicate edit ids"
    for fn in [n for n in tree.body if isinstance(n, _ast.FunctionDef)]:
        if fn.name in HOOKS: continue
        pid, _, pt = fn.name.rpartition("_")
        assert (pt in ALLOWED_POINTS and pid in ids) or fn.name.split("_", 1)[1] in ("pre_call", "post_parse", "post_exec", "pre_complete", "setup") and fn.name.split("_", 1)[0] in ids, f"unknown function {fn.name}"
    off = set(x for x in os.environ.get("BOS_EDITS_OFF", "").split(",") if x); changed = True
    while changed:
        changed = False
        for e in edits:
            if e["id"] not in off and any(d in off for d in e.get("depends", [])): off.add(e["id"]); changed = True
    active = [e for e in edits if e["id"] not in off]
    funcs = {p: [] for p in ALLOWED_POINTS}
    for e in active:
        for p in ALLOWED_POINTS:
            f = ns.get(f"{e['id']}_{p}")
            if f: funcs[p].append((e["id"], f))
    legacy = {k: ns[k] for k in HOOKS if k in ns}; consts = {k: ns[k] for k in ("HISTORY_LENGTH", "TEMPERATURE", "SETUP_CODE") if k in ns}
    return active, off, funcs, legacy, consts


def load_patch(path, quiet=False):
    """-> (funcs_by_point or None, consts). Gaia2 runs v3 patches only (EDITS); legacy 5-hook patches are rejected."""
    if path in (None, "", "none"): return None, {}
    src = open(path, encoding="utf-8").read()
    if "EDITS" not in src: raise ValueError(f"{path}: not a v3 patch (EDITS missing); legacy 5-hook patches are not supported for gaia2")
    active, off, funcs, legacy, consts = load_v3(path)
    if legacy: raise ValueError(f"{path}: legacy hooks not supported for gaia2: {sorted(legacy)}")
    if not quiet: print(f"v3 patch: active edits {[e['id'] for e in active]} off {sorted(off)}", flush=True)
    return funcs, consts


# ---------------------------------------------------------------- point runners (exceptions never reach the harness)
def run_setup(funcs, state):
    """-> list of non-empty setup code strings; a raising setup hook is recorded in state["_edit_err"] (bos_appworld_v3 rule)."""
    codes = []
    for eid, f in (funcs["setup"] if funcs else []):
        try: sc = f(); codes += [sc] if isinstance(sc, str) and sc.strip() else []
        except Exception as e: state.setdefault("_edit_err", []).append(f"{eid}:setup:{str(e)[:40]}")
    return codes


def run_text(funcs, point, val, state, si):
    """pre_call / post_parse / pre_complete: a hook returning a non-string or a blank string leaves the value unchanged."""
    for eid, f in (funcs[point] if funcs else []):
        try: v2 = f(val, state); val = v2 if isinstance(v2, str) and v2.strip() else val
        except Exception as e: si.setdefault("edit_err", []).append(f"{eid}:{point}:{str(e)[:40]}")
    return val


def run_post_exec(funcs, code, out, state, si=None):
    """si=None (replayed steps): errors are swallowed silently, as in bos_appworld_v3's replay branch."""
    for eid, f in (funcs["post_exec"] if funcs else []):
        try: f(code, out, state)
        except Exception as e:
            if si is not None: si.setdefault("edit_err", []).append(f"{eid}:post_exec:{str(e)[:40]}")
