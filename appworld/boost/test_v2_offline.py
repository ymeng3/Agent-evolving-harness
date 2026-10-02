"""Offline smoke test for CC-BOOST v2: synthetic runs, mocked proposer (BOOST_MOCK=1) and mocked judge (JUDGE_MOCK=1)."""
import json, os, subprocess, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, features as FT, loop_v2 as V2
from test_offline import synth


def main():
    d = tempfile.mkdtemp(); paths = [os.path.join(d, f"disc{s}.json") for s in (1, 2)]
    for s, p in zip((1, 2), paths): synth(p, s, f"disc{s}")
    rd = [r for r in C.load_runs(paths) if r["at_risk"]]; json.dump({r["task"]: f"instruction for {r['task']}" for r in rd}, open(os.path.join(d, "instr.json"), "w"))
    voc = FT.vocab(rd); names, desc, M = FT.pool(rd, C.L, voc); print("prog pool", len(names), M.shape, "vocab", voc)
    assert M.shape == (len(rd), len(names)) and np.isfinite(M).all()
    y = np.array([r["y"] for r in rd], float); g = [r["task"] for r in rd]; F0 = np.zeros((len(rd), 0))
    i = names.index("pagination"); lo, ln = V2.nested_cv(F0, M[:, [i]], y, g); assert ln < lo - 0.02, (lo, ln)   # planted mechanism is selectable
    rng = np.random.default_rng(0); noise = rng.normal(size=(len(rd), 50)); lo2, ln2 = V2.nested_cv(F0, noise, y, g); print("noise pool nested gain", round(lo2 - ln2, 4))
    env = {**os.environ, "BOOST_MOCK": "1", "JUDGE_MOCK": "1"}
    for arm in ("V2_PROG", "V2_FULL", "V2_SEM", "V2_SEM_UNT"):
        r = subprocess.run([sys.executable, os.path.join(HERE, "loop_v2.py"), "--arm", arm, "--disc", ",".join(paths), "--instr", os.path.join(d, "instr.json"),
                            "--out", os.path.join(d, "out"), "--rounds", "3", "--P", "3", "--judge-workers", "4"], env=env, capture_output=True, text=True)
        print(r.stdout[-900:]); assert r.returncode == 0, r.stderr[-3000:]
        st = json.load(open(os.path.join(d, "out", arm, "state.json"))); assert len(st["rounds"]) == 3
    st = json.load(open(os.path.join(d, "out", "V2_PROG", "state.json"))); assert any(a["name"] == "pagination" for a in st["admitted"]), [a["name"] for a in st["admitted"]]
    print("V2 OFFLINE TEST OK", d)


if __name__ == "__main__":
    main()
