"""CC-BOOST read-outs. usage:
  python boost/analyze.py stage1 boost/out/run1            -> BOOST vs UNTARGET vs FIXED on held-out validation (prereg sec 1)
  python boost/analyze.py stage2 F0_s1.json F0_s2.json META1.json[,META2...] RUNS_DIR   -> rubric-guided edits vs F0 (prereg sec 2)"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C


def stage1(out):
    S = {arm: json.load(open(os.path.join(out, arm, "state.json"))) for arm in ("BOOST", "UNTARGET", "FIXED") if os.path.exists(os.path.join(out, arm, "state.json"))}
    for arm, s in S.items():
        if arm != "FIXED" and s["rounds"][-1]["round"] != s.get("rounds_planned", s["rounds"][-1]["round"]):
            print(f"WARNING: {arm} stopped at round {s['rounds'][-1]['round']} of {s.get('rounds_planned')} (run incomplete)")
    for arm, s in S.items():
        print(f"\n{arm}: admitted {len(s['rubric'])} dims")
        for d in s["rubric"]: print(f"   r{d['round']} {d['name']}: {d['desc'][:110]}  (cv_gain {d.get('cv_gain')})")
        print("   round  k  disc_cv_ll  val_ll  val_auc  val_brier")
        for r in s["rounds"]: print(f"   {r['round']:5d} {r['k']:2d}  {r['disc_cv_logloss']:.4f}     {r['val']['logloss']:.4f}  {r['val']['auc']:.3f}    {r['val']['brier']:.4f}   {r.get('note', '')[:60]}")
    if "BOOST" in S:
        b = S["BOOST"]; y = np.array(b["val_y"]); g = b["val_tasks"]; lb = C.per_traj_logloss(y, np.array(b["rounds"][-1]["val_p"]))
        for other in ("UNTARGET", "FIXED"):
            if other not in S: continue
            o = S[other]; assert o["val_tasks"] == g, "validation sets differ"
            lo = C.per_traj_logloss(y, np.array(o["rounds"][-1]["val_p"])); d, lo90, hi90 = C.cluster_bootstrap_diff(g, lb, lo)
            print(f"\n{'PRIMARY' if other == 'UNTARGET' else 'SECONDARY'}: val log-loss BOOST - {other} = {d:+.4f}  90% CI [{lo90:+.4f}, {hi90:+.4f}]  "
                  f"-> {'SIGNAL (BOOST better)' if hi90 < 0 else ('BOOST worse' if lo90 > 0 else 'no signal')}")
        l0 = C.per_traj_logloss(y, np.array(b["rounds"][0]["val_p"])); d, lo90, hi90 = C.cluster_bootstrap_diff(g, lb, l0)
        print(f"BOOST final - intercept-only = {d:+.4f}  90% CI [{lo90:+.4f}, {hi90:+.4f}]")


def signflip_p(d, B=20000, seed=0):
    d = np.asarray(d, float); obs = d.mean(); rng = np.random.default_rng(seed)
    sims = (rng.choice([-1, 1], size=(B, len(d))) * d).mean(1); return float((np.abs(sims) >= abs(obs) - 1e-12).mean())


def stage2(f0a, f0b, metas, runs_dir):
    A, B = json.load(open(f0a)), json.load(open(f0b)); tasks = A["games"]
    print(f"F0 seed{A['seed']}: {sum(A['won'])}/{len(tasks)}   F0 seed{B['seed']}: {sum(B['won'])}/{len(B['games'])}   (seed-noise reference)")
    wa = dict(zip(A["games"], A["won"])); ga = dict(zip(A["games"], A["G"])); wb = dict(zip(B["games"], B["won"]))
    print(f"seed-to-seed F0 diff: {np.mean([wb[t] - wa[t] for t in tasks]):+.3f}")
    by_arm = {}
    for mp in metas.split(","):
        for m in json.load(open(mp)):
            if not m.get("valid"): continue
            rp = os.path.join(runs_dir, f"{m['pid']}_seed{A['seed']}.json")
            if not os.path.exists(rp): print("missing run", rp); continue
            R = json.load(open(rp)); assert R["games"] == tasks; wr = dict(zip(R["games"], R["won"])); gr = dict(zip(R["games"], R["G"]))
            dw = [int(wr[t]) - int(wa[t]) for t in tasks]; dg = [(gr[t] or 0) - (ga[t] or 0) for t in tasks]
            by_arm.setdefault(m["arm"], []).append((m, dw, dg))
            print(f"{m['arm']:9s} {m['pid'][:48]:48s} won {sum(R['won'])}/{len(tasks)} (F0 {sum(A['won'])})  d_won {np.mean(dw):+.3f}  G sign +{sum(x > 0 for x in dg)}/-{sum(x < 0 for x in dg)}  target={m.get('target')}")
    per_task = {}   # arm -> per-task mean over its edits of d_won; the unit of the sign-flip test is the TASK (edits share the F0 outcome)
    for arm, rows in by_arm.items():
        if len(rows) < 3: print(f"WARNING: arm {arm} has only {len(rows)} valid evaluated edits (planned 3)")
        M = np.array([r[1] for r in rows], float); per_task[arm] = M.mean(0); dg = sum((r[2] for r in rows), [])
        print(f"\nARM {arm}: {len(rows)} edits x {M.shape[1]} tasks, mean d_won {M.mean():+.3f} (task-level sign-flip p {signflip_p(per_task[arm]):.3f}), "
              f"G sign +{sum(x > 0 for x in dg)}/-{sum(x < 0 for x in dg)}")
    for a, b in (("G_BOOST", "G_RAW"), ("G_BOOST", "G_GENERIC"), ("G_RAW", "G_GENERIC")):
        if a in per_task and b in per_task:
            d = per_task[a] - per_task[b]; print(f"CONTRAST {a} - {b}: {d.mean():+.3f} (task-level paired sign-flip p {signflip_p(d):.3f}, n={len(d)} tasks)")


if __name__ == "__main__":
    if sys.argv[1] == "stage1": stage1(sys.argv[2])
    else: stage2(*sys.argv[2:6])
