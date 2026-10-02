"""CC-BOOST Stage 1b, closed loop v2 (prereg A2). Candidate pool = PROGRAMMATIC grammar features (no LLM) and/or SEMANTIC criteria
(natural language, written by the self-proposer from examples, scored by the blind judge). Selection = XGBoost second-order gain
Gain(z) = (sum g z)^2 / (2 (sum h z^2 + lambda)) for the current logistic rubric (g = p - y, h = p(1-p)); admission = NESTED grouped
CV of "pick the argmax-gain candidate on the training folds, refit, score the test fold" improving log-loss by >= MIN_GAIN.
Arms: V2_FULL (prog + targeted sem) | V2_PROG (prog only) | V2_SEM (targeted sem only) | V2_SEM_UNT (sem only, random examples).
usage: python boost/loop_v2.py --arm V2_FULL --disc A.json,B.json --instr instructions.json --out OUTDIR [--rounds 6 --P 3 --seed 0]"""
import argparse, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, features as FT, judge as JG, proposer as PR
from loop import distinct_tasks

MIN_GAIN = float(os.environ.get("BOOST_MIN_GAIN", "0.005")); LAM = 1.0
SYSTEM = ("You maintain a RUBRIC that explains why an LLM agent fails multi-app tool-use tasks (AppWorld). You add one criterion at a time, "
          "like a weak learner in gradient boosting: it must capture what the CURRENT rubric gets wrong. A separate blind rater will apply your "
          "criterion to each trajectory, seeing only the trajectory's first cells and your criterion text.")


def xgb_gain(Z, g, h, lam=LAM): return (Z.T @ g) ** 2 / (2 * ((Z ** 2).T @ h + lam))


def fit_p(F, y):
    Z, _ = C.standardize(F); w = C.fit_logit(Z, y, LAM); return w, C.predict(w, Z)


def nested_cv(F, P, y, groups, reps=3, k=5):
    """CV log-loss of the current model vs. the model after one selection step from pool P (selection redone inside every fold)."""
    ll_old, ll_new = [], []
    for rep in range(reps):
        fo = C.group_folds(groups, k, 2000 + rep); po, pn = np.zeros(len(y)), np.zeros(len(y))
        for j in range(k):
            tr, te = fo != j, fo == j
            if te.sum() == 0: continue
            Zf_tr, Zf_te = C.standardize(F[tr], F[te]); w = C.fit_logit(Zf_tr, y[tr], LAM); p_tr = C.predict(w, Zf_tr); po[te] = C.predict(w, Zf_te)
            Zp_tr, Zp_te = C.standardize(P[tr], P[te]); s = int(np.argmax(xgb_gain(Zp_tr, p_tr - y[tr], p_tr * (1 - p_tr))))
            w2 = C.fit_logit(np.hstack([Zf_tr, Zp_tr[:, [s]]]), y[tr], LAM); pn[te] = C.predict(w2, np.hstack([Zf_te, Zp_te[:, [s]]]))
        ll_old.append(C.logloss(y, po)); ll_new.append(C.logloss(y, pn))
    return float(np.mean(ll_old)), float(np.mean(ll_new))


def rubric_text(adm, w):
    if not adm: return "(empty: intercept only)"
    return "\n".join(f"- {d['name']} (weight {w[1 + j]:+.2f}; {'measured by code' if d['kind'] == 'prog' else 'rated'}): {d['desc']}" for j, d in enumerate(adm))


def sem_prompt(adm, w, examples, instr):
    ex = "\n\n".join(f"=== EXAMPLE {k + 1}: {'SUCCEEDED' if r['y'] else 'FAILED'} eventually; current rubric predicted p(success)={p:.2f} ===\n"
                     f"TASK: {instr.get(r['task'], '')[:400]}\n{C.window(r['cells'])}" for k, (r, p) in enumerate(examples))
    return (f"SETTING. In AppWorld the agent writes one python cell per step that calls app APIs; the task ends when it calls "
            f"apis.supervisor.complete_task(). Budget: 30 cells. Below are the FIRST {C.L} cells of trajectories still running at cell {C.L}, and "
            f"whether the agent eventually succeeded.\n\nCURRENT RUBRIC (logistic model of eventual success; weight < 0 means it predicts failure):\n"
            f"{rubric_text(adm, w)}\n\nEXAMPLES (eventual outcome, and the CURRENT rubric's predicted success probability):\n\n{ex}\n\n"
            f"YOUR JOB. Write ONE new yes/no CRITERION about the agent's behaviour in these cells that explains where the current rubric's predictions "
            f"are wrong (failures rated too high, successes rated too low) and that the rubric does not already capture. It must be judgeable from the "
            f"cells alone by someone who does not know the outcome; be specific and mechanistic (what the agent does or fails to do with the APIs, "
            f"their outputs and errors), not a generic quality. Do not refer to the number of cells, to complete_task, or to success itself.\n\n"
            f"OUTPUT EXACTLY two lines:\nNAME: <snake_case>\nCRITERION: <one or two sentences stating precisely when the criterion holds>")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=["V2_FULL", "V2_PROG", "V2_SEM", "V2_SEM_UNT"])
    ap.add_argument("--disc", required=True); ap.add_argument("--instr", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--rounds", type=int, default=6); ap.add_argument("--P", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--judge-workers", type=int, default=12); a = ap.parse_args()
    od = os.path.join(a.out, a.arm); os.makedirs(od, exist_ok=True)
    rd = [r for r in C.load_runs(a.disc.split(",")) if r["at_risk"]]; y = np.array([r["y"] for r in rd], float); groups = [r["task"] for r in rd]
    instr = json.load(open(a.instr)); assert all(r["task"] in instr for r in rd), "missing instructions"
    use_prog, use_sem = a.arm in ("V2_FULL", "V2_PROG"), a.arm != "V2_PROG"
    voc = FT.vocab(rd); pnames, pdesc, PM = FT.pool(rd, C.L, voc)
    keep = PM.std(0) > 1e-9; pnames = [n for n, k in zip(pnames, keep) if k]; pdesc = [d for d, k in zip(pdesc, keep) if k]; PM = PM[:, keep]
    print(f"{a.arm}: n={len(rd)} wins={int(y.sum())} prog_pool={len(pnames) if use_prog else 0} L={C.L}", flush=True)
    J = JG.Judge(os.path.join(a.out, "judge_cache"), a.judge_workers) if use_sem else None
    items = [(f"{r['tag']}|{r['seed']}|{r['task']}", instr[r["task"]][:400], C.window(r["cells"])) for r in rd]
    cands = []   # pool entries: {kind, name, desc, values(list), round_proposed}
    if use_prog: cands += [{"kind": "prog", "name": n, "desc": d, "values": PM[:, i].tolist(), "round": 0} for i, (n, d) in enumerate(zip(pnames, pdesc))]
    adm, rounds = [], []
    def save():
        json.dump({"arm": a.arm, "L": C.L, "seed": a.seed, "disc": a.disc, "vocab": voc, "min_gain": MIN_GAIN, "admitted": adm, "rounds": rounds,
                   "sem_bank": [c for c in cands if c["kind"] == "sem"], "judge_stats": J.stats if J else None}, open(os.path.join(od, "state.json"), "w"), indent=1)
    for rnd in range(1, a.rounds + 1):
        t0 = time.time(); F = np.array([d["values"] for d in adm], float).T if adm else np.zeros((len(rd), 0))
        info = {"round": rnd}
        if use_sem:   # new semantic candidates for this round
            _, p_oof = C.cv_logloss(F, y, groups); resid = y - p_oof; w_now, _ = fit_p(F, y)
            fails, succ = [i for i in range(len(rd)) if y[i] == 0], [i for i in range(len(rd)) if y[i] == 1]
            if a.arm == "V2_SEM_UNT":
                rng = random.Random(1000 * a.seed + rnd); f_order, s_order = rng.sample(fails, len(fails)), rng.sample(succ, len(succ))
            else:
                f_order, s_order = sorted(fails, key=lambda i: resid[i]), sorted(succ, key=lambda i: -resid[i])
            pf = distinct_tasks(f_order, rd, 4); used = {rd[i]["task"] for i in pf}; ps = distinct_tasks([i for i in s_order if rd[i]["task"] not in used], rd, 2)
            order = pf + ps; random.Random(1000 * a.seed + rnd).shuffle(order)
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": sem_prompt(adm, w_now, [(rd[i], p_oof[i]) for i in order], instr)}]
            with ThreadPoolExecutor(a.P) as ex: outs = list(ex.map(lambda _: PR.safe_chat(msgs), range(a.P)))
            new, plog = [], []
            for text, use in outs:
                nm, crit = PR.field(text, "NAME")[:60], PR.field(text, "CRITERION")[:500]
                ok = 20 <= len(crit) and crit not in {c.get("desc") for c in cands}
                plog.append({"name": nm, "criterion": crit, "usage": use, "ok": ok})
                if not ok: continue
                maj, votes = J.score(crit, items); none = sum(m is None for m in maj); vals = [np.nan if m is None else float(m) for m in maj]
                pos = sum(1 for v in vals if v == 1); neg = sum(1 for v in vals if v == 0)
                agree = np.mean([len(set(x for x in v.values() if x is not None)) == 1 for v in votes.values() if sum(x is not None for x in v.values()) >= 2])
                plog[-1].update(present=pos, absent=neg, unjudged=none, vote_agreement=float(agree))
                if none > 0.2 * len(rd) or min(pos, neg) < 3: plog[-1]["ok"] = False; continue
                c = {"kind": "sem", "name": nm or f"sem_r{rnd}", "desc": crit, "values": vals, "round": rnd, "vote_agreement": float(agree)}; cands.append(c); new.append(c["name"])
            info.update(proposals=plog, new_sem=new, examples=[rd[i]["task"] for i in order])
        pool = [c for c in cands if not any(c is d for d in adm)]
        if not pool: info.update(note="empty pool"); rounds.append(info); save(); continue
        P = np.array([c["values"] for c in pool], float).T
        ll_old, ll_new = nested_cv(F, P, y, groups); w, p = fit_p(F, y)
        Zp, _ = C.standardize(P); gains = xgb_gain(Zp, p - y, p * (1 - p)); top = np.argsort(-gains)[:10]; best = int(top[0])
        info.update(nested_cv_old=ll_old, nested_cv_new=ll_new, nested_gain=ll_old - ll_new, top_gains=[(pool[i]["kind"], pool[i]["name"], float(gains[i])) for i in top])
        if ll_old - ll_new >= MIN_GAIN:
            pool[best]["admitted_round"] = rnd; adm.append(pool[best]); info["note"] = f"ADMIT {pool[best]['kind']}:{pool[best]['name']} (nested gain {ll_old - ll_new:.4f})"
        else:
            info["note"] = f"no admission (nested gain {ll_old - ll_new:.4f}; best {pool[best]['kind']}:{pool[best]['name']})"
        info["secs"] = round(time.time() - t0, 1); rounds.append(info); save()
        print(f"  round {rnd}: {info['note']}  [{info['secs']}s]", flush=True)
    save()


if __name__ == "__main__":
    main()
