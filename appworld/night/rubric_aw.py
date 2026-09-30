"""Evolving-rubric A/B/C on AppWorld challenge (round 2). usage: rubric_aw.py propose | score STEPS_BASE_TAG
propose: gpt-4o diagnoses 12 failure windows (from CH27_F0 seed 1) with A raw | B fixed rubric | C rubric evolved on the other failures;
proposes K=6 patches per condition against the bare AppWorld harness; writes patches_rubric_aw/RB{A,B,C}k.py + jobs."""
import json, os, re, sys, time
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
os.environ.setdefault("LL_PARENT", "x"); import lean_loop as L
R = "/net/scratch/ymeng3/bos_appworld"; PD = f"{R}/patches_rubric_aw"; os.makedirs(PD, exist_ok=True); os.makedirs(f"{R}/night/rubric", exist_ok=True)
BASE = "HISTORY_LENGTH = 20\nTEMPERATURE = 0.4\n"
def window(tr, t, before=3, after=4): return "\n".join(f"[cell {s['step']}] {s['code'][:200]}\n -> {s['out'][:140]}" for s in tr[max(0, t - before): t + after])
def propose_ops(context, K, prefix):
    cands = []; att = 0; log = []
    sysm = A.PROPOSER_SYS.replace("embodied household tasks (ALFWorld)", "multi-app tool-use tasks (AppWorld: the model writes python cells that call app APIs)")
    while len(cands) < K and att < 2 * K:
        att += 1
        user = f"{L.AW_API_DOC}\n\nCURRENT HARNESS PATCH (bare; output a COMPLETE module):\n```python\n{BASE}\n```\n\n{context}\n\nAlready proposed: {[c[0] for c in cands]}. Propose ONE new patch. Add a line 'TARGET: <what it fixes>'."
        try: resp = A.gpt4o([{"role": "system", "content": sysm}, {"role": "user", "content": user}], temperature=1.0, max_tokens=1800)
        except Exception as e: log.append(str(e)[:100]); time.sleep(5); continue
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp); src = ("\n".join(l for l in m.group(1).strip().splitlines() if not re.match(r"\s*(TARGET|NAME|COMPOSITION_HYPOTHESIS)\s*:", l)) + "\n") if m else None
        ok, why = (A.validate_patch(src) if src else (False, "no code")); log.append({"att": att, "ok": ok, "why": why})
        if not ok: continue
        pid = f"{prefix}{len(cands)+1}_{(nm.group(1) if nm else 'cand')[:24]}"; p = f"{PD}/{pid}.py"; open(p, "w").write(src); cands.append((pid, p))
    json.dump(log, open(f"{R}/night/rubric/log_{prefix}.json", "w"), indent=1); return cands
if sys.argv[1] == "propose":
    r = json.load(open(f"{R}/results/CH27_F0_seed1.json")); meta = json.load(open(f"{R}/night/meta.json"))
    lost = [t for t, w in zip(r["games"], r["won"]) if not w]; traj = dict(zip(r["games"], r["traj"]))
    fails, disc = lost[:12], lost[12:]
    def win(t): return f"TASK: {meta[t]['instruction']}\n" + window(traj[t], meta[t]["t_branch"])
    raw = "\n\n".join(f"[failure {i+1}]\n{win(t)}" for i, t in enumerate(fails))
    FIXED = ("RUBRIC (fixed):\n1. API choice: did the agent call the API that matches the task's verb and object?\n2. Data completeness: did it fetch all pages / all items before filtering, and apply every constraint in the task?\n"
             "3. Completion check: did it verify results against the task before complete_task, and finish within the step budget?\nFor each dimension give PASS/WARN/FAIL with a one-line evidence quote.")
    def diagnose(rubric, t):
        try: return A.gpt4o([{"role": "user", "content": f"Diagnose this failed tool-use trajectory with the rubric.\n{rubric}\n\n{win(t)}\n\nOutput the per-dimension verdicts only."}], temperature=0.2, max_tokens=500)
        except Exception as e: return f"(judge error {str(e)[:60]})"
    rubric = FIXED; log = []
    for rnd in range(2):
        sample = disc[rnd*6:(rnd+1)*6]; diags = [(t, diagnose(rubric, t)) for t in sample]
        p = (f"You maintain a diagnostic rubric for failures of an LLM tool-use agent. Current rubric:\n{rubric}\n\nFailures diagnosed with it:\n" + "\n\n".join(f"[case]\n{win(t)}\nDIAGNOSIS: {d}" for t, d in diags) +
             "\n\nWhich failure mechanisms does the rubric MISS or blur? Propose edits: ADD (new dimension + evaluation rule + evidence), REFINE, MERGE, PRUNE. Keep at most 5 dimensions. Output the NEW rubric in the same format, then a line 'CHANGES: ...'.")
        try: rr = A.gpt4o([{"role": "user", "content": p}], temperature=0.5, max_tokens=900)
        except Exception as e: rr = rubric + f"\nCHANGES: (error {str(e)[:60]})"
        rubric = rr.split("CHANGES:")[0].strip() or rubric; log.append({"round": rnd, "rubric": rubric, "changes": rr.split("CHANGES:")[-1][:600]})
    json.dump(log, open(f"{R}/night/rubric/evolution_log.json", "w"), indent=1); open(f"{R}/night/rubric/evolved_rubric.txt", "w").write(rubric); print("EVOLVED RUBRIC:\n", rubric, flush=True)
    diagB = {t: diagnose(FIXED, t) for t in fails}; diagC = {t: diagnose(rubric, t) for t in fails}
    ctx = {"A": "FAILURE TRAJECTORIES of the current harness:\n\n" + raw + "\n\nPropose ONE change that fixes a failure mechanism you see.",
           "B": "FAILURE TRAJECTORIES with a rubric diagnosis:\n\n" + "\n\n".join(f"[failure {i+1}]\n{win(t)}\nDIAGNOSIS (fixed rubric):\n{diagB[t]}" for i, t in enumerate(fails)) + "\n\nPropose ONE change that fixes a diagnosed failure mechanism.",
           "C": f"FAILURE TRAJECTORIES with a rubric diagnosis. Rubric:\n{rubric}\n\n" + "\n\n".join(f"[failure {i+1}]\n{win(t)}\nDIAGNOSIS:\n{diagC[t]}" for i, t in enumerate(fails)) + "\n\nPropose ONE change that fixes a diagnosed failure mechanism."}
    out = {lab: propose_ops(c, 6, f"RB{lab}") for lab, c in ctx.items()}
    with open(f"{R}/night/rubric/jobs_s1.txt", "w") as f:
        for lab in out:
            for pid, p in out[lab]: f.write(f"{pid} {p} 1 50\n")
    print({lab: [p for p, _ in v] for lab, v in out.items()}, "spent", round(A.GUARD.spent(), 2))
else:
    base_tag = sys.argv[2]; import glob, statistics as st
    def wm(t, s):
        f = f"{R}/results/{t}_seed{s}.json"; return dict(zip(json.load(open(f))["games"], json.load(open(f))["won"])) if os.path.exists(f) else None
    b = {s: wm(base_tag, s) for s in (1, 2)}; print(f"baseline {base_tag}: s1 {sum(b[1].values()) if b[1] else None} s2 {sum(b[2].values()) if b[2] else None}")
    print(f"{'cond':10s} n  n(s1>=+2)  mean_d_s1  max_d_s1   confirmed(s2>=base)  per-op")
    for lab, name in (("A", "A raw"), ("B", "B fixed"), ("C", "C evolved")):
        rows = []
        for p in sorted(glob.glob(f"{PD}/RB{lab}*.py")):
            pid = os.path.basename(p)[:-3]; w1 = wm(pid, 1); w2 = wm(pid, 2)
            if not w1 or not b[1]: continue
            d1 = sum(w1.values()) - sum(b[1].values()); d2 = (sum(w2.values()) - sum(b[2].values())) if (w2 and b[2]) else None; rows.append((pid[:26], d1, d2))
        if not rows: print(name, "no results"); continue
        print(f"{name:10s} {len(rows)}  {sum(r[1]>=2 for r in rows)}          {st.mean(r[1] for r in rows):+5.1f}     {max(r[1] for r in rows):+3d}      {sum(1 for r in rows if r[2] is not None and r[2]>=0 and r[1]>=2)}                 {rows}")
