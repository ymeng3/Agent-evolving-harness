"""Offline test for CC-BOOST Stage 1c (loop_pw.py, prereg A5). Synthetic runs with a planted CONFOUNDER and a planted MECHANISM:
task family (fixed per task) decides which app is called AND the base rate; within a task, success depends on pagination (random per run).
On validation the family base rates are reversed. Pooled selection should prefer the family feature; pairwise must pick pagination and
transfer to validation pairs. Also checks the pairwise maths (gain = Newton decrease, logistic recovery) and runs every arm with mocks."""
import json, os, random, subprocess, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, features as FT, loop_pw as PW, loop_v2 as V2


def synth_conf(path, seed, tag, n=40, flip=False):
    rng = random.Random(seed); games, won, traj = [], [], []
    for t in range(n):
        fam = t % 2; easy = (fam == 0) != flip; app = "spotify" if fam == 0 else "amazon"
        pag = rng.random() < 0.5; p_win = (0.85 if easy else 0.12) + (0.12 if pag else -0.1)
        w = rng.random() < max(0.02, min(0.97, p_win)); T = rng.randint(17, 30) if w else 30; steps = []
        for i in range(T):
            code = rng.choice(["print(apis.api_docs.show_app_descriptions())", f"tok = apis.{app}.login(username=u, password=p)",
                               f"r = apis.{app}.search_items(query='x'" + (", page_index=1)" if pag and rng.random() < 0.5 else ")")])
            if w and i == T - 1: code = "apis.supervisor.complete_task()"
            steps.append({"step": i, "code": code, "out": "{...}", "exec_error": int(rng.random() < 0.1), "resp": "...", "gp": 3, "gf": 1})
        games.append(f"task{t:02d}"); won.append(w); traj.append(steps)
    json.dump({"tag": tag, "seed": seed, "games": games, "won": won, "traj": traj, "crashed": [None] * n}, open(path, "w"))


def main():
    rng = np.random.default_rng(0)
    # 1. maths: pairwise fit recovers a planted coefficient; the gain equals the one-step Newton decrease of the ridge pair loss
    n_t, per = 150, 4; x = rng.normal(size=n_t * per); a_t = np.repeat(rng.normal(scale=2, size=n_t), per); grp = np.repeat(np.arange(n_t), per)
    y = (rng.random(len(x)) < 1 / (1 + np.exp(-(a_t + 1.2 * x)))).astype(int)
    recs = [{"task": f"t{g}", "won": int(v)} for g, v in zip(grp, y)]; I, J, T = PW.make_pairs(recs)
    assert all(recs[i]["task"] == recs[j]["task"] and recs[i]["won"] == 1 and recs[j]["won"] == 0 for i, j in zip(I, J))
    Z = (x / x.std()).reshape(-1, 1); w = PW.fit_pw(Z, I, J, lam=1e-6); assert 0.6 < w[0] / x.std() < 2.0, w
    g = PW.gains(Z, np.zeros(len(I)), I, J, lam=1.0)[0]; d = (Z[I] - Z[J])[:, 0]; G, H = np.sum(PW.sig(0) - 1) * 0 + np.sum(-0.5 * d), np.sum(0.25 * d * d)
    assert abs(g - G ** 2 / (2 * (H + 1.0))) < 1e-9
    # a task-level feature (constant within task) has exactly zero pairwise gain
    zt = np.repeat(rng.normal(size=n_t), per).reshape(-1, 1); assert PW.gains(zt, np.zeros(len(I)), I, J)[0] < 1e-12
    # 2. confounded synthetic runs
    dd = tempfile.mkdtemp(); disc = [os.path.join(dd, f"disc{s}.json") for s in range(1, 5)]; val = [os.path.join(dd, f"val{s}.json") for s in (1, 2, 3)]
    for s, p in enumerate(disc, 1): synth_conf(p, s, f"disc{s}")
    for s, p in enumerate(val, 1): synth_conf(p, 100 + s, f"val{s}", flip=True)
    rd = [r for r in C.load_runs(disc) if r["at_risk"]]; json.dump({f"task{t:02d}": f"instruction {t}" for t in range(40)}, open(os.path.join(dd, "instr.json"), "w"))
    I, J, T = PW.make_pairs(rd); voc = FT.vocab(rd); names, _, M = FT.pool(rd, C.L, voc); keep = M.std(0) > 1e-9; names = [n_ for n_, k in zip(names, keep) if k]; M = M[:, keep]
    yv = np.array([r["y"] for r in rd]); Zm, _ = C.standardize(M); w0, p0 = V2.fit_p(np.zeros((len(rd), 0)), yv)
    pooled_top = names[int(np.argmax(V2.xgb_gain(Zm, p0 - yv, p0 * (1 - p0))))]
    pw_top = names[int(np.argmax(PW.gains(Zm, np.zeros(len(I)), I, J)))]
    print(f"n={len(rd)} pairs={len(I)} | pooled argmax gain: {pooled_top} | pairwise argmax gain: {pw_top}")
    gp = V2.xgb_gain(Zm, p0 - yv, p0 * (1 - p0)); gw = PW.gains(Zm, np.zeros(len(I)), I, J); a_, b_ = names.index("app_spotify"), names.index("pagination")
    print(f"pooled gain: family feature {gp[a_]:.2f} vs mechanism {gp[b_]:.2f} | pairwise gain: family {gw[a_]:.3f} vs mechanism {gw[b_]:.2f}")
    assert gp[a_] > gp[b_], "test is not confounded: pooled gain does not prefer the family feature"
    assert gw[a_] < 0.25 * gw[b_], "pairwise gain does not discount the family feature"
    assert pw_top == "pagination", pw_top
    env = {**os.environ, "BOOST_MOCK": "1", "JUDGE_MOCK": "1"}; out = os.path.join(dd, "out")
    for arm in ("PW_PROG", "PW_FULL", "PW_SEM", "PW_SEM_UNT"):
        r = subprocess.run([sys.executable, os.path.join(HERE, "loop_pw.py"), "--arm", arm, "--disc", ",".join(disc), "--instr", os.path.join(dd, "instr.json"),
                            "--out", out, "--rounds", "3", "--P", "3", "--judge-workers", "4"], env=env, capture_output=True, text=True)
        print(r.stdout[-700:]); assert r.returncode == 0, r.stderr[-3000:]
        r = subprocess.run([sys.executable, os.path.join(HERE, "loop_pw.py"), "score", os.path.join(out, arm, "state.json"), "--val", ",".join(val),
                            "--instr", os.path.join(dd, "instr.json"), "--workers", "4"], env=env, capture_output=True, text=True)
        print(r.stdout[-500:]); assert r.returncode == 0, r.stderr[-3000:]
    st = json.load(open(os.path.join(out, "PW_PROG", "state.json"))); assert st["admitted"] and st["admitted"][0]["name"] == "pagination", [a["name"] for a in st["admitted"]]
    assert st["rounds"][0]["val"]["pair_acc"] > 0.6, st["rounds"][0]["val"]
    print("PW OFFLINE TEST OK", dd)


if __name__ == "__main__":
    main()
