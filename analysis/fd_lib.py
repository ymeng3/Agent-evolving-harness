"""Shared helpers for the failure-driven / rubric overnight pipelines (2026-09-25). Proposer = gpt-4o via OpenRouter (bos_alfworld.gpt4o)."""
import json, re, os, sys, time
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld"); import bos_alfworld as A
R = "/net/scratch/ymeng3/bos_alfworld"; BASE = open(f"{R}/patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py").read()
def window(tr, t, before=6, after=15):
    return "\n".join(f"step {s['step']}: {s['action'][:60]} -> {s['obs'][:100]}" for s in tr[max(0, t - before): t + after])
def propose_ops(context, K, prefix, outdir, sys_extra="", log_path=None, temperature=1.0):
    """Ask the proposer for K patches (full modules based on BASE). Returns list of (pid, path). Static-checked; up to 2K attempts."""
    os.makedirs(outdir, exist_ok=True); cands = []; log = []; attempts = 0
    sysmsg = A.PROPOSER_SYS + sys_extra
    while len(cands) < K and attempts < 2 * K:
        attempts += 1
        user = (f"[proposal attempt {attempts}]\n{A.HARNESS_API_DOC}\n\nCURRENT HARNESS PATCH (your output must be a COMPLETE module that keeps this behaviour except for your change):\n```python\n{BASE}\n```\n\n"
                f"{context}\n\nNames of your earlier proposals (do not repeat their idea): {json.dumps([c[0] for c in cands])}\n\nPropose ONE new patch.")
        try: resp = A.gpt4o([{"role": "system", "content": sysmsg}, {"role": "user", "content": user}], temperature=temperature, max_tokens=1800)
        except Exception as e: log.append({"attempt": attempts, "err": str(e)[:200]}); time.sleep(5); continue
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp); tg = re.search(r"TARGET:\s*([^\n]+)", resp)
        name = (nm.group(1)[:40] if nm else f"unnamed{attempts}"); src = m.group(1).strip() if m else None
        ok, why = (A.validate_patch(src) if src else (False, "no code"))
        if ok:
            try: ns = {}; exec(compile(src, name, "exec"), ns)
            except Exception as e: ok, why = False, f"exec: {e}"
        log.append({"attempt": attempts, "name": name, "ok": ok, "why": why, "target": tg.group(1)[:200] if tg else "", "resp": resp[:4000]})
        if not ok: continue
        pid = f"{prefix}{len(cands)+1}_{name}"; p = f"{outdir}/{pid}.py"; open(p, "w").write(f"# TARGET: {tg.group(1)[:200] if tg else 'unspecified'}\n" + src); cands.append((pid, p))
    if log_path: json.dump(log, open(log_path, "w"), indent=1)
    return cands
def net_table(tags, seeds, ctag, manifest_key, results=f"{R}/results"):
    """mean success over seeds for each tag, minus C. Returns {tag: (mean, per-seed list)}."""
    def sr(t, s):
        f = f"{results}/{t}_seed{s}.json"
        return json.load(open(f))["success_rate"] * 100 if os.path.exists(f) else None
    out = {}
    c = [sr(ctag, s) for s in seeds]
    for t in tags:
        v = [sr(t, s) for s in seeds]; out[t] = (v, c)
    return out
