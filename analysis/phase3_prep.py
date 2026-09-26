"""Phase 3 prep: write candidate/parent job lines, per-unit LOO patches (ast drop + validate), window-ablation wrappers."""
import ast, json, os, sys
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_alfworld"; P3 = f"{R}/patches_p3"; os.makedirs(P3, exist_ok=True)
CANDS = {  # key: (candidate patch, parent patch, units)
 "r6": (f"{P3}/P3_ours_r6_strategic_memory_fallbac.py", f"{R}/patches_loop/CL_O_r5_c4_S.py", ["retry_policy", "memory_update", "choose_fallback"]),
 "n5": (f"{P3}/P3_naive_r5_context_focus_with_feedb.py", f"{R}/patches_loop/CL_N_r4_c1.py", ["retry_policy", "format_prompt", "HISTORY_LENGTH"]),
 "r2": (f"{P3}/P3_ours_r2_history_retry_memory.py", f"{R}/patches_loop/CL_N_r1_c1_S.py", ["retry_policy", "memory_update", "HISTORY_LENGTH"]),
}
LOCAL = {"choose_fallback", "retry_policy", "parse_action"}
def drop(src, unit):
    t = ast.parse(src); keep = []
    for n in t.body:
        if isinstance(n, ast.FunctionDef) and n.name == unit: continue
        if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == unit for x in n.targets): continue
        keep.append(n)
    t.body = keep; return ast.unparse(t)
def gate(src, unit, mode, k=15):
    """window ablation inside the same hook (no extra top-level names): 'late_off' = active only for the first k calls; 'early_off' = only after."""
    t = ast.parse(src); cnt = "_n_" + unit[:2]
    for n in t.body:
        if isinstance(n, ast.FunctionDef) and n.name == unit:
            a0 = n.args.args[0].arg if unit == "format_prompt" else n.args.args[0].arg   # prompt / state
            st = "state" if unit == "format_prompt" else n.args.args[0].arg
            ret = a0 if unit == "format_prompt" else "None"
            cond = f"{st}['{cnt}'] <= {k}" if mode == "late_off" else f"{st}['{cnt}'] > {k}"
            pre = ast.parse(f"{st}['{cnt}'] = {st}.get('{cnt}', 0) + 1\nif not ({cond}):\n    return {ret}\n").body
            n.body = pre + n.body
    return ast.unparse(t)
jobs1 = []; units = {}; win = []
for key, (cp, pp, U) in CANDS.items():
    for tag, p in ((f"P3C_{key}", cp), (f"P3P_{key}", pp)): jobs1.append(f"{tag} {p} 1 48")
    src = open(cp).read()
    for u in U:
        s = drop(src, u); ok, why = A.validate_patch(s)
        if not ok: print("LOO invalid", key, u, why); continue
        op = f"{P3}/P3C_{key}_loo_{u[:6]}.py"; open(op, "w").write(s + "\n"); units[f"{key}:{u}"] = {"cand": key, "unit": u, "kind": "local" if u in LOCAL else "global", "C": cp, "OFF": op, "Ctag": f"P3C_{key}"}
    for u in U:
        if u in ("format_prompt", "memory_update") and len(win) < 4:
            for mode in ("late_off", "early_off"):
                s = gate(src, u, mode); ok, why = A.validate_patch(s)
                if not ok: print("window invalid", key, u, mode, why); continue
                wp = f"{P3}/P3W_{key}_{u[:6]}_{mode}.py"; open(wp, "w").write(s + "\n"); win.append(f"P3W_{key}_{u[:6]}_{mode} {wp} 1 32")
open(f"{P3}/jobs_step1.txt", "w").write("\n".join(jobs1) + "\n"); json.dump(units, open(f"{P3}/units.json", "w"), indent=1); open(f"{P3}/jobs_window.txt", "w").write("\n".join(win) + "\n")
print("step1 jobs", len(jobs1), "| units", {k: v["kind"] for k, v in units.items()}, "| window jobs", len(win))
