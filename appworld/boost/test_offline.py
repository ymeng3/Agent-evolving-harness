"""Offline smoke test for CC-BOOST: synthetic results files + mocked proposer (BOOST_MOCK=1). No server, no AppWorld.
Checks: landmark filtering, no goal-check leakage into cells, sandbox rejects forbidden code, model/CV sanity, loop runs all arms."""
import json, os, random, subprocess, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C


def synth(path, seed, tag, n=50):
    rng = random.Random(seed); games, won, traj = [], [], []
    for t in range(n):
        pag = rng.random() < 0.5; errp = rng.choice([0.05, 0.3]); p_win = 0.15 + 0.5 * pag - 0.3 * (errp > 0.1) + 0.2
        w = rng.random() < max(0.02, min(0.95, p_win)); T = rng.randint(8, 30) if w else 30
        steps = []
        for i in range(T):
            code = rng.choice(["print(apis.api_docs.show_app_descriptions())", "tok = apis.spotify.login(username=u, password=p)",
                               "r = apis.amazon.search_products(query='x'" + (", page_index=1)" if pag and rng.random() < 0.4 else ")")])
            if w and i == T - 1: code = "apis.supervisor.complete_task()"
            steps.append({"step": i, "code": code, "out": "[]" if rng.random() < 0.2 else "{...}", "exec_error": int(rng.random() < errp), "resp": "...", "gp": 3, "gf": 1})
        games.append(f"task{t:02d}"); won.append(w); traj.append(steps)
    json.dump({"tag": tag, "seed": seed, "games": games, "won": won, "traj": traj, "crashed": [None] * n}, open(path, "w"))


def main():
    d = tempfile.mkdtemp(); paths = {}
    for name, seed in (("disc1", 1), ("disc2", 2), ("val1", 3), ("val2", 4)): paths[name] = os.path.join(d, f"{name}.json"); synth(paths[name], seed, name)
    recs = C.load_runs([paths["disc1"]])
    assert all(set(c) == {"i", "code", "out", "error", "reply"} for r in recs for c in r["cells"]), "goal-check fields leaked into cells"
    assert all(len(r["cells"]) <= C.L for r in recs)
    assert all(not r["at_risk"] or (r["n_cells"] > C.L and not any("complete_task" in c["code"] for c in r["cells"])) for r in recs)
    for bad in ("import os\ndef detect(steps): return 0", "def detect(steps): return open('x')", "def detect(steps): return steps.__class__", "def f(s): return 1"):
        try: C.compile_detector(bad); raise AssertionError(f"sandbox accepted: {bad!r}")
        except ValueError: pass
    y = np.array([0, 0, 1, 1, 0, 1, 1, 0], float); assert abs(C.auc(y, [0.1, 0.2, 0.8, 0.9, 0.3, 0.7, 0.6, 0.4]) - 1.0) < 1e-9
    assert abs(C.auc(y, [0.5] * 8) - 0.5) < 1e-9
    rng = np.random.default_rng(0); x = rng.normal(size=400); yy = (rng.random(400) < 1 / (1 + np.exp(-(0.3 + 1.5 * x)))).astype(float)
    w = C.fit_logit(C.standardize(x.reshape(-1, 1))[0], yy, lam=1e-6); assert abs(w[1] / x.std() - 1.5) < 0.4, w
    g = [i // 2 for i in range(400)]; cv0, _ = C.cv_logloss(np.zeros((400, 0)), yy, g); cv1, _ = C.cv_logloss(x.reshape(-1, 1), yy, g)
    assert cv1 < cv0 - 0.05, (cv0, cv1)
    env = {**os.environ, "BOOST_MOCK": "1"}; out = os.path.join(d, "out")
    for arm in ("FIXED", "BOOST", "UNTARGET"):
        r = subprocess.run([sys.executable, os.path.join(HERE, "loop.py"), "--arm", arm, "--disc", f"{paths['disc1']},{paths['disc2']}", "--val", f"{paths['val1']},{paths['val2']}",
                            "--out", out, "--rounds", "3", "--P", "3"], env=env, capture_output=True, text=True)
        print(r.stdout[-1500:]); assert r.returncode == 0, r.stderr[-3000:]
        st = json.load(open(os.path.join(out, arm, "state.json"))); assert st["rounds"], arm
    st = json.load(open(os.path.join(out, "BOOST", "state.json")))
    assert any(c["name"] == "uses_pagination" for c in st["rubric"]), "boosting failed to admit the planted mechanism"
    print("OFFLINE TEST OK", out)


if __name__ == "__main__":
    main()
