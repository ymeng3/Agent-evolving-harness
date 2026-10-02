"""CC-BOOST Stage 1c (prereg A5): the rubric as a WITHIN-TASK PAIRWISE booster = XGBoost rank:pairwise with query group = task.
Rubric score s(x) = sum_k w_k z_k(x), no intercept (a task-level offset cancels in every pair). Pairs = (i, j) of the same task with
won_i = 1, won_j = 0. Loss = mean over pairs of -log sigma(s_i - s_j) (Bradley-Terry on trajectories). Gain of a standardized candidate
z: d = z_i - z_j, g = sigma(m) - 1, h = sigma(m)(1 - sigma(m)), Gain = (sum g d)^2 / (2 (sum h d^2 + lambda)), so between-task variation
in z earns nothing. Admission = nested task-grouped CV of the selection step on held-out tasks' pairs, >= MIN_GAIN nats.
Arms: PW_FULL (prog + sem from misranked pairs) | PW_PROG (prog only, no LLM) | PW_SEM (sem, misranked pairs) | PW_SEM_UNT (sem, random pairs).
usage: python boost/loop_pw.py --arm PW_FULL --disc A.json,B.json,... --instr instructions.json --out OUTDIR [--rounds 6 --P 3 --seed 0]
       python boost/loop_pw.py score OUT/ARM/state.json --val V1.json,V2.json --instr instructions.json   (validation read-out)"""
import argparse, collections, itertools, json, os, random, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, features as FT, judge as JG, proposer as PR
from loop_v2 import SYSTEM

MIN_GAIN = float(os.environ.get("BOOST_MIN_GAIN", "0.005")); LAM = 1.0; LN2 = float(np.log(2))


def make_pairs(recs):
    """-> (I, J, task_of_pair): every same-task (winner, loser) combination."""
    by = collections.defaultdict(list)
    for i, r in enumerate(recs): by[r["task"]].append(i)
    I, J, T = [], [], []
    for t, ix in by.items():
        for a, b in itertools.combinations(ix, 2):
            if recs[a]["won"] == recs[b]["won"]: continue
            w, l = (a, b) if recs[a]["won"] else (b, a); I.append(w); J.append(l); T.append(t)
    return np.array(I, int), np.array(J, int), T


def sig(x): return 1 / (1 + np.exp(-np.clip(x, -30, 30)))


def fit_pw(Z, I, J, lam=LAM, iters=100):
    """ridge pairwise logistic by Newton on pair differences, no intercept; -> w (k,)."""
    D = Z[I] - Z[J]; k = Z.shape[1]; w = np.zeros(k)
    if k == 0 or len(I) == 0: return w
    for _ in range(iters):
        p = sig(D @ w); step = np.linalg.solve((D * (p * (1 - p))[:, None]).T @ D + lam * np.eye(k), D.T @ (p - 1) + lam * w); w -= step
        if np.abs(step).max() < 1e-9: break
    return w


def pair_loss(m): return -np.log(np.clip(sig(m), 1e-6, 1))   # per-pair loss at margin m


def gains(Zp, m, I, J, lam=LAM):
    D = Zp[I] - Zp[J]; p = sig(m); g, h = p - 1, p * (1 - p)
    return (D.T @ g) ** 2 / (2 * ((D ** 2).T @ h + lam))


def zfull(F, rows):
    """standardize every trajectory's features with the statistics of the training rows only."""
    if F.shape[1] == 0: return np.zeros((len(F), 0))
    return C.standardize(F[rows], F)[1]


def task_folds(I, groups, k, seed):
    fo = C.group_folds(groups, k, seed); return fo, fo[I]   # fold of each trajectory, fold of each pair (= its task's fold)


def oof_margins(F, I, J, groups, reps=3, k=5):
    m = np.zeros(len(I))
    for rep in range(reps):
        fo, fp = task_folds(I, groups, k, 3000 + rep)
        for j in range(k):
            trp, tep = fp != j, fp == j
            if tep.sum() == 0: continue
            Z = zfull(F, fo != j); w = fit_pw(Z, I[trp], J[trp]); m[tep] += ((Z[I[tep]] - Z[J[tep]]) @ w) / reps
    return m


def nested_cv(F, P, I, J, groups, reps=3, k=5):
    """held-out-task mean pair loss of the current rubric vs. after one selection step from pool P (selection redone in every fold)."""
    lo, ln = [], []
    for rep in range(reps):
        fo, fp = task_folds(I, groups, k, 2000 + rep); po, pn = np.zeros(len(I)), np.zeros(len(I))
        for j in range(k):
            trp, tep = fp != j, fp == j
            if tep.sum() == 0: continue
            Zf = zfull(F, fo != j); w = fit_pw(Zf, I[trp], J[trp]); m_tr = (Zf[I[trp]] - Zf[J[trp]]) @ w
            po[tep] = (Zf[I[tep]] - Zf[J[tep]]) @ w
            Zp = zfull(P, fo != j); s = int(np.argmax(gains(Zp, m_tr, I[trp], J[trp])))
            Z2 = np.hstack([Zf, Zp[:, [s]]]); w2 = fit_pw(Z2, I[trp], J[trp]); pn[tep] = (Z2[I[tep]] - Z2[J[tep]]) @ w2
        lo.append(pair_loss(po).mean()); ln.append(pair_loss(pn).mean())
    return float(np.mean(lo)), float(np.mean(ln))


def rubric_text(adm, w):
    if not adm: return "(empty: every trajectory scores 0)"
    return "\n".join(f"- {d['name']} (weight {w[j]:+.2f}; {'measured by code' if d['kind'] == 'prog' else 'rated'}): {d['desc']}" for j, d in enumerate(adm))


def sem_prompt(adm, w, pairs, rd, instr):
    blocks = []
    for k, (i, j, m) in enumerate(pairs):
        blocks.append(f"=== PAIR {k + 1}: two attempts at the SAME task; current rubric score difference (better - worse) = {m:+.2f} "
                      f"({'WRONG order' if m < 0 else 'right order, weakly'}) ===\nTASK: {instr.get(rd[i]['task'], '')[:400]}\n"
                      f"--- ATTEMPT A (this one SUCCEEDED eventually) ---\n{C.window(rd[i]['cells'])}\n"
                      f"--- ATTEMPT B (this one FAILED eventually) ---\n{C.window(rd[j]['cells'])}")
    return (f"SETTING. In AppWorld the agent writes one python cell per step that calls app APIs; the task ends when it calls "
            f"apis.supervisor.complete_task(). Budget: 30 cells. Below are PAIRS of attempts by the same agent at the same task: the FIRST {C.L} "
            f"cells of each attempt (both still running at cell {C.L}), and which attempt eventually succeeded. Because both attempts face the "
            f"same task, the difference between them is in how the agent behaved, not in how hard the task is.\n\n"
            f"CURRENT RUBRIC (a score; higher should mean the better attempt; weight < 0 means the dimension counts against an attempt):\n"
            f"{rubric_text(adm, w)}\n\nPAIRS (with the current rubric's score difference; negative = it prefers the attempt that failed):\n\n"
            + "\n\n".join(blocks) +
            f"\n\nYOUR JOB. Write ONE new yes/no CRITERION about the agent's behaviour in these cells that separates the succeeding attempt from the "
            f"failing attempt of the same task, where the current rubric gets the order wrong, and that the rubric does not already capture. It is "
            f"applied to ONE attempt at a time, so it must be judgeable from a single attempt's cells by someone who does not know the outcome; be "
            f"specific and mechanistic (what the agent does or fails to do with the APIs, their outputs and errors), not a generic quality. Do not "
            f"refer to the number of cells, to complete_task, to the other attempt, or to success itself.\n\n"
            f"OUTPUT EXACTLY two lines:\nNAME: <snake_case>\nCRITERION: <one or two sentences stating precisely when the criterion holds>")


def pick_pairs(order, I, T, n):
    out, seen = [], set()
    for q in order:
        if T[q] in seen: continue
        out.append(q); seen.add(T[q])
        if len(out) == n: break
    return out


def items_of(recs, instr): return [(f"{r['tag']}|{r['seed']}|{r['task']}", instr[r["task"]][:400], C.window(r["cells"])) for r in recs]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--arm", required=True, choices=["PW_FULL", "PW_PROG", "PW_SEM", "PW_SEM_UNT"])
    ap.add_argument("--disc", required=True); ap.add_argument("--instr", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--rounds", type=int, default=6); ap.add_argument("--P", type=int, default=3); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--judge-workers", type=int, default=12); a = ap.parse_args()
    od = os.path.join(a.out, a.arm); os.makedirs(od, exist_ok=True)
    rd = [r for r in C.load_runs(a.disc.split(",")) if r["at_risk"]]; groups = [r["task"] for r in rd]; I, J, T = make_pairs(rd)
    instr = json.load(open(a.instr)); assert all(r["task"] in instr for r in rd), "missing instructions"
    use_prog, use_sem = a.arm in ("PW_FULL", "PW_PROG"), a.arm != "PW_PROG"
    voc = FT.vocab(rd); pnames, pdesc, PM = FT.pool(rd, C.L, voc)
    keep = PM.std(0) > 1e-9; pnames = [n for n, k in zip(pnames, keep) if k]; pdesc = [d for d, k in zip(pdesc, keep) if k]; PM = PM[:, keep]
    print(f"{a.arm}: n={len(rd)} tasks={len(set(groups))} pairs={len(I)} (tasks with a pair {len(set(T))}) prog_pool={len(pnames) if use_prog else 0} L={C.L}", flush=True)
    if len(I) < 20: sys.exit(f"only {len(I)} within-task pairs: too few to fit or validate anything")
    J_ = JG.Judge(os.path.join(a.out, "judge_cache"), a.judge_workers) if use_sem else None; items = items_of(rd, instr)
    cands = []
    if use_prog: cands += [{"kind": "prog", "name": n, "desc": d, "values": PM[:, i].tolist(), "round": 0} for i, (n, d) in enumerate(zip(pnames, pdesc))]
    adm, rounds = [], []
    def save():
        json.dump({"arm": a.arm, "objective": "pairwise_within_task", "L": C.L, "seed": a.seed, "disc": a.disc, "vocab": voc, "min_gain": MIN_GAIN,
                   "n": len(rd), "n_pairs": len(I), "admitted": adm, "rounds": rounds, "sem_bank": [c for c in cands if c["kind"] == "sem"],
                   "judge_stats": J_.stats if J_ else None}, open(os.path.join(od, "state.json"), "w"), indent=1)
    for rnd in range(1, a.rounds + 1):
        t0 = time.time(); F = np.array([d["values"] for d in adm], float).T if adm else np.zeros((len(rd), 0)); info = {"round": rnd}
        if use_sem:
            m_oof = oof_margins(F, I, J, groups); w_now = fit_pw(zfull(F, np.ones(len(rd), bool)), I, J)
            tie = np.random.default_rng(1000 * a.seed + rnd).random(len(I))   # round 1 has all margins 0: break ties at random, not by task order
            order = list(np.lexsort((tie, np.round(m_oof, 9)))) if a.arm != "PW_SEM_UNT" else random.Random(1000 * a.seed + rnd).sample(range(len(I)), len(I))
            sel = pick_pairs(order, I, T, 3); random.Random(1000 * a.seed + rnd).shuffle(sel)
            msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": sem_prompt(adm, w_now, [(I[q], J[q], m_oof[q]) for q in sel], rd, instr)}]
            with ThreadPoolExecutor(a.P) as ex: outs = list(ex.map(lambda _: PR.safe_chat(msgs), range(a.P)))
            if all(str(u.get("finish", "")).startswith("error") for _, u in outs):
                save(); sys.exit(f"round {rnd}: all {a.P} proposer calls failed: {outs[0][1].get('finish')}")
            new, plog, todo = [], [], []
            for text, use in outs:
                nm, crit = PR.field(text, "NAME")[:60], PR.field(text, "CRITERION")[:500]
                ok = 20 <= len(crit) and crit not in {c.get("desc") for c in cands} and crit not in {t[1] for t in todo}
                plog.append({"name": nm, "criterion": crit, "usage": use, "ok": ok})
                if ok: todo.append((len(plog) - 1, crit, nm))
            with ThreadPoolExecutor(max(1, len(todo))) as ex: scored = list(ex.map(lambda t: J_.score(t[1], items), todo))
            for (pi, crit, nm), (maj, votes) in zip(todo, scored):
                none = sum(m is None for m in maj); vals = [np.nan if m is None else float(m) for m in maj]
                pos = sum(1 for v in vals if v == 1); neg = sum(1 for v in vals if v == 0)
                agree = np.mean([len(set(x for x in v.values() if x is not None)) == 1 for v in votes.values() if sum(x is not None for x in v.values()) >= 2])
                plog[pi].update(present=pos, absent=neg, unjudged=none, vote_agreement=float(agree))
                if none > 0.2 * len(rd) or min(pos, neg) < 3: plog[pi]["ok"] = False; continue
                c = {"kind": "sem", "name": nm or f"sem_r{rnd}", "desc": crit, "values": vals, "round": rnd, "vote_agreement": float(agree)}; cands.append(c); new.append(c["name"])
            info.update(proposals=plog, new_sem=new, example_pairs=[[rd[I[q]]["tag"], rd[J[q]]["tag"], T[q]] for q in sel])
        pool = [c for c in cands if not any(c is d for d in adm)]
        if not pool: info.update(note="empty pool"); rounds.append(info); save(); continue
        P = np.array([c["values"] for c in pool], float).T
        ll_old, ll_new = nested_cv(F, P, I, J, groups); allr = np.ones(len(rd), bool)
        Zf = zfull(F, allr); w = fit_pw(Zf, I, J); m = (Zf[I] - Zf[J]) @ w
        gs = gains(zfull(P, allr), m, I, J); top = np.argsort(-gs)[:10]; best = int(top[0])
        info.update(nested_cv_old=ll_old, nested_cv_new=ll_new, nested_gain=ll_old - ll_new, top_gains=[(pool[i]["kind"], pool[i]["name"], float(gs[i])) for i in top])
        if ll_old - ll_new >= MIN_GAIN:
            pool[best]["admitted_round"] = rnd; adm.append(pool[best]); info["note"] = f"ADMIT {pool[best]['kind']}:{pool[best]['name']} (nested gain {ll_old - ll_new:.4f})"
        else:
            info["note"] = f"no admission (nested gain {ll_old - ll_new:.4f}; best {pool[best]['kind']}:{pool[best]['name']})"
        info["secs"] = round(time.time() - t0, 1); rounds.append(info); save()
        print(f"  round {rnd}: {info['note']}  [{info['secs']}s]", flush=True)
    save()


def score(state_path, val, instr_path, workers=12, B=2000):
    """validation read-out on within-task validation pairs: fit on ALL discovery pairs with the dimensions admitted up to each round."""
    s = json.load(open(state_path)); assert s["L"] == C.L
    rd = [r for r in C.load_runs(s["disc"].split(",")) if r["at_risk"]]; rv = [r for r in C.load_runs(val.split(",")) if r["at_risk"]]
    I, J, _ = make_pairs(rd); Iv, Jv, Tv = make_pairs(rv); instr = json.load(open(instr_path))
    print(f"{s['arm']}: validation n={len(rv)} pairs={len(Iv)} over {len(set(Tv))} tasks")
    if len(Iv) == 0: sys.exit("no validation pairs (need >= 2 validation runs per task)")
    names, _, VM = FT.pool(rv, C.L, tuple(s["vocab"])); Jd = None; vcols = []
    for d in s["admitted"]:
        if d["kind"] == "prog": vcols.append(VM[:, names.index(d["name"])])
        else:
            Jd = Jd or JG.Judge(os.path.join(os.path.dirname(os.path.dirname(state_path)), "judge_cache"), workers)
            maj, _ = Jd.score(d["desc"], items_of(rv, instr)); vcols.append(np.array([np.nan if m is None else float(m) for m in maj]))
    for rec in s["rounds"]:
        idx = [j for j, d in enumerate(s["admitted"]) if d["admitted_round"] <= rec["round"]]
        Fd = np.array([s["admitted"][j]["values"] for j in idx], float).T if idx else np.zeros((len(rd), 0))
        Fv = np.array([vcols[j] for j in idx], float).T if idx else np.zeros((len(rv), 0))
        if idx: Zd, Zv = C.standardize(Fd, Fv)
        else: Zd, Zv = np.zeros((len(rd), 0)), np.zeros((len(rv), 0))
        w = fit_pw(Zd, I, J); mv = (Zv[Iv] - Zv[Jv]) @ w
        rec["val"] = {"pair_logloss": float(pair_loss(mv).mean()), "pair_acc": float(np.mean((mv > 0) + 0.5 * (mv == 0))), "n_pairs": int(len(Iv))}
        rec["val_margins"] = mv.tolist()
        print(f"  round {rec['round']}: k={len(idx)} val pair_ll={rec['val']['pair_logloss']:.4f} (null {LN2:.4f}) pair_acc={rec['val']['pair_acc']:.3f}")
    mv = np.array(s["rounds"][-1]["val_margins"]) if s["rounds"] else np.zeros(len(Iv))
    lo, hi = boot(Tv, (mv > 0) + 0.5 * (mv == 0), B); dl, dlo, dhi = C.cluster_bootstrap_diff(Tv, pair_loss(mv), np.full(len(mv), LN2), B)
    print(f"  final: pair_acc 90% CI [{lo:.3f}, {hi:.3f}]; pair_ll - null = {dl:+.4f} 90% CI [{dlo:+.4f}, {dhi:+.4f}]")
    s.update(val=val, val_pairs=[[int(i), int(j), t] for i, j, t in zip(Iv, Jv, Tv)], val_pair_tasks=Tv, val_judge_stats=Jd.stats if Jd else None)
    if os.path.exists(state_path): os.replace(state_path, state_path + ".bak")
    json.dump(s, open(state_path, "w"), indent=1)


def boot(groups, x, B=2000, seed=0):
    groups = np.asarray(groups); u = sorted(set(groups.tolist())); idx = {g: np.nonzero(groups == g)[0] for g in u}; rng = np.random.default_rng(seed); st = []
    for _ in range(B):
        ii = np.concatenate([idx[u[j]] for j in rng.choice(len(u), len(u), replace=True)]); st.append(np.mean(np.asarray(x)[ii]))
    return float(np.quantile(st, 0.05)), float(np.quantile(st, 0.95))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("state"); ap.add_argument("--val", required=True); ap.add_argument("--instr", required=True)
        ap.add_argument("--workers", type=int, default=12); x = ap.parse_args(); score(x.state, x.val, x.instr, x.workers)
    else:
        main()
