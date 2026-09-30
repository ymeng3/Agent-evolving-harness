"""Phase 2 pilot search: NAIVE vs FAILURE-CONDITIONED generation on the same 10 failure records. Writes patches_v3/P2_{arm}_{k}.py
(v3 format), candidates.json with metadata + validity flags. usage: search.py [K=10]"""
import json, os, re, sys, collections, time
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); sys.path.insert(0, "/net/scratch/ymeng3/bos_appworld/phase2"); import bos_alfworld as A; from schema import *
R = "/net/scratch/ymeng3/bos_appworld"; PD = f"{R}/patches_v3"; os.makedirs(PD, exist_ok=True); K = int(sys.argv[1]) if len(sys.argv) > 1 else 10
bank = json.load(open(f"{R}/phase2/failure_bank.json")); r = json.load(open(f"{R}/results/CH27_F0_seed1.json")); traj = dict(zip(r["games"], r["traj"]))
# select K records with diverse (capability, implementation) addresses, round-robin over addresses by frequency
by = collections.defaultdict(list)
for fm in bank: by[(fm["capability"], fm["implementation"])].append(fm)
order = sorted(by, key=lambda k: -len(by[k])); sel = []; i = 0
while len(sel) < K and any(by.values()):
    k = order[i % len(order)]; i += 1
    if by[k]: sel.append(by[k].pop(0))
json.dump(sel, open(f"{R}/phase2/selected10.json", "w"), indent=1)
IFACE = open(f"{R}/bos_appworld_v3.py").read().split('"""')[1]
SPACE = ("SEARCH SPACE: an edit is (capability in {Planning, Memory, ToolUse, Recovery, Verification}) x (implementation in {Prompt, State, Code, ControlFlow}) attached to a control point. "
         "Harness-executed implementations act WITHOUT relying on the model: State = the harness maintains/injects structured state; Code = the harness rewrites or post-processes the model's code / API results (e.g. rewrite a page_index=0 call into a loop over pages); "
         "ControlFlow = the harness changes what executes when (e.g. block the first complete_task while required actions are missing). Prompt edits change the model's decision by text and are allowed only when the mechanism genuinely needs model-side behaviour.")
FORMAT = ("OUTPUT FORMAT: first a line 'NAME: <snake_case>', then ONE python code block containing a complete v3 patch module: EDITS = [ {\"id\": \"e1\", \"capability\": ..., \"impl\": ..., \"trigger\": <when it fires>, \"depends\": [], \"expected_effect\": ..., \"side_effect_risk\": ...}, ... ] "
          "and functions named <id>_setup() -> str | <id>_pre_call(prompt, state) -> str | <id>_post_parse(code, state) -> str | <id>_post_exec(code, out, state) -> None | <id>_pre_complete(code, state) -> str. "
          "Allowed imports: re, json, math, random, collections, itertools, string (import inside functions). No file/network access. Use 1-3 edits: the MINIMAL executable repair; do not add edits merely to make a compound. "
          "Every edit must state its trigger condition explicitly and must not fire outside it.")
def window(tr, lo, hi): return "\n".join(f"[cell {s['step']}] {s['code'][:240]}\n -> {s['out'][:180]}" for s in tr[lo:hi])
def ctx_traj(fm):
    tr = traj[fm["task"]]; n = len(tr); return f"TASK: {fm['instruction']}\nOUTCOME: failed (goal checks {fm['G'] or 0:.2f})\nFIRST CELLS:\n{window(tr,0,4)}\nLAST CELLS:\n{window(tr,max(0,n-12),n)}"
def propose(arm, fm, k):
    if arm == "naive":
        user = f"{IFACE}\n\n{SPACE}\n\nPARENT HARNESS: bare (no edits).\n\nHere is a failed trajectory of the current agent:\n{ctx_traj(fm)}\n\nPropose an improvement to the harness that would help. {FORMAT}"
    else:
        user = (f"{IFACE}\n\n{SPACE}\n\nPARENT HARNESS: bare (no edits).\n\nFAILURE MECHANISM (diagnosed, with evidence):\n{json.dumps({x: fm[x] for x in FM_FIELDS}, indent=1)}\n\nTRAJECTORY:\n{ctx_traj(fm)}\n\n"
                f"Produce the minimal executable repair for THIS mechanism, intervening at the diagnosed capability x implementation x control point (deviate only with a stated reason). Prefer harness-executed State/Code/ControlFlow interventions. Prompt-only edits only if model-side behaviour is genuinely required. {FORMAT}")
    for att in range(3):
        try: resp = A.gpt4o([{"role": "system", "content": "You are a careful engineer improving an LLM agent harness through small, executable, well-triggered edits."}, {"role": "user", "content": user}], temperature=1.0, max_tokens=2200)
        except Exception as e: time.sleep(5); continue
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp)
        if not m: continue
        src = "\n".join(l for l in m.group(1).strip().splitlines() if not re.match(r"\s*(NAME|TARGET)\s*:", l)) + "\n"
        pid = f"P2_{arm}_{k}_{(nm.group(1) if nm else 'cand')[:22]}"; p = f"{PD}/{pid}.py"; open(p, "w").write(src)
        try:
            os.environ.pop("BOS_EDITS_OFF", None); sys.path.insert(0, R); import importlib, bos_appworld_v3 as V; importlib.reload(V); active, off, funcs, legacy, consts = V.load_v3(p)
            edits = [{x: e.get(x) for x in EDIT_FIELDS} for e in active]; return {"pid": pid, "path": p, "arm": arm, "task": fm["task"], "mechanism": fm["mechanism"], "address": (fm["capability"], fm["implementation"], fm["control_point"]), "edits": edits, "n_edits": len(edits), "valid": True, "why": "ok", "resp": resp[:3000]}
        except Exception as e: last = f"{type(e).__name__}: {str(e)[:120]}"; user += f"\n\nYour previous attempt failed validation: {last}. Fix it and output again."
    return {"pid": pid if 'pid' in dir() else f"P2_{arm}_{k}", "path": None, "arm": arm, "task": fm["task"], "mechanism": fm["mechanism"], "edits": [], "n_edits": 0, "valid": False, "why": last if 'last' in dir() else "no code"}
def mechanistic(e):
    """validity check: an edit is NON-mechanistic if it is Prompt-only without an explicit trigger, or its trigger is generic."""
    trig = str(e.get("trigger") or "").lower(); generic = trig in ("", "always", "every step", "each step", "all steps") or len(trig) < 15
    return not (e.get("impl") == "Prompt" and generic)
cands = []
for k, fm in enumerate(sel):
    for arm in ("naive", "fc"):
        c = propose(arm, fm, k); c["mechanistic_edits"] = sum(mechanistic(e) for e in c["edits"]); c["impls"] = [e.get("impl") for e in c["edits"]]; cands.append(c)
        print(f"{c['pid']:40s} valid={c['valid']} n_edits={c['n_edits']} impls={c['impls']} mechanistic={c['mechanistic_edits']} | {c['why'][:60]}", flush=True)
json.dump(cands, open(f"{R}/phase2/candidates.json", "w"), indent=1)
v = [c for c in cands if c["valid"]]
print("\nsummary:", {arm: {"valid": sum(1 for c in v if c["arm"] == arm), "compound(|C|>1)": sum(1 for c in v if c["arm"] == arm and c["n_edits"] > 1), "prompt-only": sum(1 for c in v if c["arm"] == arm and c["impls"] and all(i == "Prompt" for i in c["impls"])), "all-mechanistic": sum(1 for c in v if c["arm"] == arm and c["mechanistic_edits"] == c["n_edits"] and c["n_edits"] > 0)} for arm in ("naive", "fc")}, "spent", round(A.GUARD.spent(), 2))
