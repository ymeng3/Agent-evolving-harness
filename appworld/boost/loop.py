"""CC-BOOST Stage 1: the rubric as gradient boosting (prereg docs/preregs/CC_BOOST_RUBRIC_PREREG.md section 1).
Each round: fit the ridge-logistic rubric on discovery landmark trajectories, take out-of-fold pseudo-residuals r = y - p, show the
self-proposer examples (BOOST: largest |r|; UNTARGET: random, same counts and format), get P candidate detectors, admit the one with
the best grouped-CV log-loss gain if gain >= MIN_GAIN. FIXED = hand-written generic detectors, no proposer.
usage: python boost/loop.py --arm BOOST|UNTARGET|FIXED --disc results/A_seed1.json,... --val results/B_seed1.json,... --out boost/out/run1"""
import argparse, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, proposer as PR

MIN_GAIN = float(os.environ.get("BOOST_MIN_GAIN", "0.005"))
try: GIT = __import__("subprocess").run(["git", "-C", os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
except Exception: GIT = None
SYSTEM = ("You maintain an executable RUBRIC that explains why an LLM agent fails multi-app tool-use tasks (AppWorld). Each rubric dimension "
          "is a small Python detector over the agent's first cells. You add one dimension at a time, like a weak learner in gradient boosting: "
          "it must capture what the CURRENT rubric gets wrong.")


def instructions(task_ids, cache):
    """fetch task instructions once (atomic write, shared by all arms); fail loudly if any is missing so arms cannot differ."""
    have = json.load(open(cache)) if os.path.exists(cache) else {}
    miss = [t for t in task_ids if t not in have]
    if miss and os.environ.get("BOOST_ALLOW_NO_INSTR") != "1":
        from appworld import AppWorld
        for t in miss:
            with AppWorld(task_id=t, experiment_name="cc_boost_instr", random_seed=1) as w: have[t] = w.task.instruction
        tmp = cache + f".tmp{os.getpid()}"; json.dump(have, open(tmp, "w"), indent=1); os.replace(tmp, cache)
        miss = [t for t in task_ids if t not in have]
        if miss: sys.exit(f"instructions missing for {len(miss)} tasks")
    return have


def distinct_tasks(cands, recs, n):
    """first n candidates with at most one trajectory per task (both arms), so BOOST cannot spend slots on two seeds of one task."""
    out, seen = [], set()
    for i in cands:
        if recs[i]["task"] in seen: continue
        out.append(i); seen.add(recs[i]["task"])
        if len(out) == n: break
    return out


def rubric_text(rubric, w):
    if not rubric: return "(empty: intercept only)"
    return "\n".join(f"- {d['name']} (weight {w[1 + j]:+.2f}): {d['desc']}" for j, d in enumerate(rubric))


def example_block(k, r, p, instr):
    return (f"=== EXAMPLE {k}: {'SUCCEEDED' if r['won'] else 'FAILED'} eventually; current rubric predicted p(success)={p:.2f} ===\n"
            f"TASK: {instr.get(r['task'], '(instruction unavailable)')[:400]}\n{C.window(r['cells'])}")


def build_prompt(rubric, w, examples, instr):
    ex = "\n\n".join(example_block(k + 1, r, p, instr) for k, (r, p) in enumerate(examples))
    return (f"SETTING. In AppWorld the agent writes one python cell per step that calls app APIs (apis.<app>.<api>(...)); the task ends when it "
            f"calls apis.supervisor.complete_task(). Budget: 30 cells. You see only the FIRST {C.L} cells of trajectories that were still running at "
            f"cell {C.L}, and whether the agent eventually succeeded.\n\n"
            f"DETECTOR CONTRACT. Write `def detect(steps) -> float`. steps = list of up to {C.L} dicts with keys 'i' (cell index), 'code' (str, the "
            f"executed cell), 'out' (str, first 200 chars of its output), 'error' (bool, execution failed), 'reply' (str, last 600 chars of the "
            f"model's raw reply). Return a number (0/1 flag, count or rate); larger = the mechanism is more present. Allowed imports: re, json, math, "
            f"random, collections, itertools, string (import inside the function). No file or network access. It must never raise. Do NOT use the "
            f"number of cells or whether complete_task was called (every trajectory here is still running at cell {C.L}).\n\n"
            f"CURRENT RUBRIC (logistic model of eventual success on standardised detector values; weight < 0 means the mechanism predicts failure):\n"
            f"{rubric_text(rubric, w)}\n\nEXAMPLES (eventual outcome, and the CURRENT rubric's predicted success probability):\n\n{ex}\n\n"
            f"YOUR JOB. Find ONE concrete, recurring behaviour visible in these cells that explains where the current rubric's predictions are wrong "
            f"(failures it rates too high, successes it rates too low) and that the rubric does not already measure. Prefer specific, mechanistic "
            f"behaviours (what the agent does or fails to do with the APIs, their outputs and errors) over generic qualities. Implement it as a detector.\n\n"
            f"OUTPUT EXACTLY:\nNAME: <snake_case>\nDESCRIPTION: <one line: what it measures and why it predicts failure or success>\n"
            f"```python\ndef detect(steps):\n    ...\n```")


def matrix(rubric, key, n): return np.array([d[key] for d in rubric], dtype=float).T if rubric else np.zeros((n, 0))


def validate(src, rd, rv):
    fn = C.compile_detector(src); vd, ed = C.run_detector(fn, rd); vv, ev = C.run_detector(fn, rv)
    if ed > 0.05 * len(rd): raise ValueError(f"errors on {ed}/{len(rd)} discovery trajectories")
    ok = vd[~np.isnan(vd)]
    if len(set(np.round(ok, 9).tolist())) < 2: raise ValueError("constant on the discovery set")
    vals, cnt = np.unique(np.round(ok, 9), return_counts=True)
    if len(vals) == 2 and cnt.min() < 3: raise ValueError(f"fires on fewer than 3 trajectories ({cnt.min()})")
    return vd, vv, ed, ev


def gen(msgs):
    t0 = time.time(); text, use = PR.safe_chat(msgs); return text, use, round(time.time() - t0, 1)


def parse_validate(text, rd, rv):
    """main thread only (the detector sandbox uses SIGALRM). -> (candidate or None, why)"""
    src = PR.last_block(text, "def detect")
    try:
        if not src: raise ValueError("no python block with def detect")
        vd, vv, ed, ev = validate(src, rd, rv)
        return {"name": PR.field(text, "NAME")[:60] or "unnamed", "desc": PR.field(text, "DESCRIPTION")[:300], "src": src, "vd": vd.tolist(), "vv": vv.tolist(), "err_d": ed, "err_v": ev}, "ok"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"


def propose(prompt, rd, rv, P, log):
    """P proposals in parallel; an invalid one gets one serial repair attempt with the validation error as feedback."""
    msgs0 = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    with ThreadPoolExecutor(P) as ex: outs = list(ex.map(lambda _: gen(msgs0), range(P)))
    cands = []
    for text, use, secs in outs:
        c, why = parse_validate(text, rd, rv); log.append({"att": 0, "usage": use, "secs": secs, "ok": c is not None, "why": why})
        if c is None:
            text2, use2, secs2 = gen(msgs0 + [{"role": "assistant", "content": text[-6000:]}, {"role": "user", "content": f"Your detector failed validation: {why}. Fix it and output again in the same format."}])
            c, why2 = parse_validate(text2, rd, rv); log.append({"att": 1, "usage": use2, "secs": secs2, "ok": c is not None, "why": why2})
        if c: cands.append(c)
    return cands


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=["BOOST", "UNTARGET", "FIXED"]); ap.add_argument("--disc", required=True); ap.add_argument("--val", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--rounds", type=int, default=6); ap.add_argument("--P", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(); od = os.path.join(a.out, a.arm); os.makedirs(od, exist_ok=True)
    rd = [r for r in C.load_runs(a.disc.split(",")) if r["at_risk"]]; rv = [r for r in C.load_runs(a.val.split(",")) if r["at_risk"]]
    yd = np.array([r["y"] for r in rd], dtype=float); gd = [r["task"] for r in rd]; yv = np.array([r["y"] for r in rv], dtype=float)
    print(f"{a.arm}: discovery landmark n={len(rd)} (wins {int(yd.sum())}), validation landmark n={len(rv)} (wins {int(yv.sum())}), L={C.L}", flush=True)
    instr = instructions(sorted(set(gd)), os.path.join(a.out, "instructions.json"))
    rubric, rounds, plog = [], [], []
    if a.arm == "FIXED":
        for name, (desc, src) in C.FIXED_DETECTORS.items():
            try: vd, vv, ed, ev = validate(src, rd, rv)
            except ValueError as e: print(f"  FIXED detector {name} skipped: {e}", flush=True); continue
            rubric.append({"name": name, "desc": desc, "src": src, "vd": vd.tolist(), "vv": vv.tolist(), "round": 0})
    def snapshot(rnd, extra):
        Fd, Fv = matrix(rubric, "vd", len(rd)), matrix(rubric, "vv", len(rv)); cv, _ = C.cv_logloss(Fd, yd, gd)
        m, pv = C.fit_eval(Fd, yd, Fv, yv)
        rec = {"round": rnd, "k": len(rubric), "disc_cv_logloss": cv, "val": {x: m[x] for x in ("logloss", "auc", "brier")}, "w": m["w"], "val_p": pv.tolist(), **extra}
        rounds.append(rec); print(f"  round {rnd}: k={len(rubric)} disc_cv_ll={cv:.4f} val_ll={m['logloss']:.4f} val_auc={m['auc']:.3f} {extra.get('note', '')}", flush=True)
        json.dump({"arm": a.arm, "L": C.L, "min_gain": MIN_GAIN, "seed": a.seed, "rounds_planned": a.rounds, "disc": a.disc, "val": a.val, "model": os.environ.get("BOS_MODEL"), "git": GIT, "val_tasks": [r["task"] for r in rv], "val_y": yv.tolist(), "rubric": [{k: d[k] for k in ("name", "desc", "src", "round")} | {"cv_gain": d.get("cv_gain")} for d in rubric],
                   "rounds": rounds, "proposer_log": plog}, open(os.path.join(od, "state.json"), "w"), indent=1)
    snapshot(0, {"note": "initial"})
    if a.arm == "FIXED": return
    for rnd in range(1, a.rounds + 1):
        Fd = matrix(rubric, "vd", len(rd)); base_cv, p_oof = C.cv_logloss(Fd, yd, gd); resid = yd - p_oof
        w_now = C.fit_eval(Fd, yd, matrix(rubric, "vv", len(rv)), yv)[0]["w"]
        fails, succ = [i for i in range(len(rd)) if rd[i]["won"] == 0], [i for i in range(len(rd)) if rd[i]["won"] == 1]
        if a.arm == "BOOST":
            f_order = sorted(fails, key=lambda i: resid[i]); s_order = sorted(succ, key=lambda i: -resid[i])
        else:
            rng = random.Random(1000 * a.seed + rnd); f_order = rng.sample(fails, len(fails)); s_order = rng.sample(succ, len(succ))
        pick_f = distinct_tasks(f_order, rd, 4); used = {rd[i]["task"] for i in pick_f}
        pick_s = distinct_tasks([i for i in s_order if rd[i]["task"] not in used], rd, 2)
        order = pick_f + pick_s; random.Random(1000 * a.seed + rnd).shuffle(order)
        prompt = build_prompt(rubric, w_now, [(rd[i], p_oof[i]) for i in order], instr); rlog = []
        cands = propose(prompt, rd, rv, a.P, rlog)
        scored = []
        for c in cands:
            cv_new, _ = C.cv_logloss(np.hstack([Fd, np.array(c["vd"]).reshape(-1, 1)]), yd, gd); c["cv_gain"] = base_cv - cv_new; scored.append(c)
        plog.append({"round": rnd, "examples": [rd[i]["task"] for i in order], "attempts": rlog, "candidates": [{"name": c["name"], "desc": c["desc"], "cv_gain": c["cv_gain"], "src": c["src"]} for c in scored]})
        best = max(scored, key=lambda c: c["cv_gain"]) if scored else None
        if best and best["cv_gain"] >= MIN_GAIN:
            best["round"] = rnd; rubric.append(best); note = f"ADMIT {best['name']} gain={best['cv_gain']:.4f}"
        else:
            note = f"no admission (best gain {best['cv_gain']:.4f})" if best else "no valid candidate"
        snapshot(rnd, {"note": note, "n_valid": len(scored)})


if __name__ == "__main__":
    main()
