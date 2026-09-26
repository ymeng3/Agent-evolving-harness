"""KG-A feature extraction. FROZEN. Own-source features come ONLY from the patch text; NOTHING from
the candidate's own smoke record may be used as a feature (that record IS the label).
Per KGA_PREREG.md sha ec3fa570cfeabc8b, leakage ban #1: no task-outcome quantity anywhere."""
import ast, json, re, hashlib, os, collections

HOOKS = ("format_prompt", "parse_action", "retry_policy", "memory_update", "choose_fallback")
ROOT = "/net/scratch/ymeng3/bos_alfworld"

def _depth(node, d=0):
    m = d
    for ch in ast.iter_child_nodes(node):
        if isinstance(ch, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            m = max(m, _depth(ch, d + 1))
        else:
            m = max(m, _depth(ch, d))
    return m

def own_source_features(src):
    """C1. Deterministic function of the patch text alone."""
    f = collections.OrderedDict()
    try: tree = ast.parse(src)
    except SyntaxError:
        return None, {}
    defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for h in HOOKS: f["has_" + h] = 1.0 if h in defs else 0.0
    f["n_hooks"] = float(sum(1 for h in HOOKS if h in defs))
    lines = src.splitlines()
    f["loc"] = float(len([l for l in lines if l.strip() and not l.strip().startswith("#")]))
    f["nbytes"] = float(len(src))
    seglens = []
    for h, n in defs.items():
        if h in HOOKS: seglens.append(float((n.end_lineno or n.lineno) - n.lineno + 1))
    f["max_hook_loc"] = max(seglens) if seglens else 0.0
    f["mean_hook_loc"] = sum(seglens) / len(seglens) if seglens else 0.0
    cnt = collections.Counter(type(n).__name__ for n in ast.walk(tree))
    for k in ("Try", "ExceptHandler", "For", "While", "If", "ListComp", "DictComp", "SetComp",
              "GeneratorExp", "Lambda", "Return", "Raise", "Assert", "Subscript", "Compare",
              "BoolOp", "Call", "Dict", "Set", "List", "JoinedStr"):
        f["n_" + k] = float(cnt.get(k, 0))
    f["max_nesting"] = float(_depth(tree))
    attrs = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
    ac = collections.Counter(attrs)
    for k in ("get", "append", "add", "setdefault", "pop", "items", "keys", "values",
              "lower", "strip", "split", "join", "search", "match", "findall", "sub"):
        f["attr_" + k] = float(ac.get(k, 0))
    # state read / write asymmetry: the write-only-bookkeeping signature
    rd = wr = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "state":
            if isinstance(n.ctx, ast.Store): wr += 1
            else: rd += 1
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "state" and n.attr in ("get", "setdefault"):
            rd += 1
    f["state_reads"] = float(rd); f["state_writes"] = float(wr)
    f["state_write_only"] = 1.0 if (wr > 0 and rd == 0) else 0.0
    f["state_rw_ratio"] = float(rd) / (wr + 1.0)
    # declared constants
    H = T = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try: val = ast.literal_eval(n.value)
            except Exception: continue
            if n.targets[0].id == "HISTORY_LENGTH": H = val
            if n.targets[0].id == "TEMPERATURE": T = val
    f["declares_H"] = 1.0 if H is not None else 0.0
    f["declares_T"] = 1.0 if T is not None else 0.0
    f["H_val"] = float(H) if isinstance(H, (int, float)) else 5.0
    f["T_val"] = float(T) if isinstance(T, (int, float)) else 0.4
    f["const_out_of_range"] = 0.0
    try:
        if (H is not None and not 0 <= int(H) <= 20) or (T is not None and not 0.0 <= float(T) <= 1.0):
            f["const_out_of_range"] = 1.0
    except Exception: f["const_out_of_range"] = 1.0
    # a literal-string fallback return, the N01 signature
    f["literal_return"] = float(sum(1 for n in ast.walk(tree)
                                    if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)
                                    and isinstance(n.value.value, str)))
    # does retry_policy consult admissibility at all
    f["retry_uses_adm"] = 0.0
    if "retry_policy" in defs:
        seg = ast.dump(defs["retry_policy"])
        f["retry_uses_adm"] = 1.0 if ("admissible" in seg or "adm" in seg) else 0.0
    f["n_names"] = float(len({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}))
    # edit-instance identity per hook: sha of the whitespace-normalised segment
    shas = {}
    for h, n in defs.items():
        if h not in HOOKS: continue
        seg = "\n".join(lines[n.lineno - 1:(n.end_lineno or n.lineno)])
        seg = re.sub(r"#.*", "", seg)
        seg = " ".join(seg.split())
        shas[h] = hashlib.sha256(seg.encode()).hexdigest()[:16]
    return f, shas
