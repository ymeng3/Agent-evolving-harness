"""Offline test of depth-wise tree growth (boost/bit_grow.py; docs/design/BIT_DEPTHWISE.md). No server, no AppWorld, no LLM (BOOST_MOCK=1).
Synthetic data with a planted structure: a block_once parent ("an answer passed to complete_task") fires on 8 states of a seed-1 base log;
5 action tasks are helped (the block rescues them), 3 question tasks (their text contains '?', logged won) are harmed. The branch build is
made by bit_branch build and its result files are fabricated. The mock proposer returns the child "'?' not in task" (plus an always-true
child that must fail the self-check and an invalid one that is fixed on retry). Asserts: node stats, the child's self-check, positive
in-node Gain (= 5.375 exactly), kept-leaf P(a>0) >= 0.9, the 3 harmed states dropped (value removed = +3), and a held-out build on a seed-2
log that contains no node episode.
usage (from the repo root): py appworld/boost/test_bit_grow.py"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

PARENT = {"name": "block_answer_any_task", "kind": "block_once", "cls": "task_knowledge",
          "hypothesis": "synthetic parent: an answer passed to complete_task is wrong on action tasks.",
          "note": "This task asks you to DO something. If it is done, call apis.supervisor.complete_task() without an answer.",
          "detect_src": "def detect(view):\n    import re\n    m = re.search(r\"complete_task\\(\\s*answer\\s*=\\s*([^)]*)\\)\", view[\"pending\"] or \"\")\n"
                        "    return bool(m) and m.group(1).strip() != \"None\"\n",
          "origin": {"case_id": None, "run": "SYN"}}
ACT = {f"act{i:03d}_1": f"Send ${10 * i} to contact number {i} on venmo and note it in my diary." for i in range(1, 9)}
QST = {f"qst{i:03d}_1": f"How many songs are in my playlist number {i}?" for i in range(1, 6)}
NOF = {f"nof{i:03d}_1": f"Delete all my alarms of week {i}." for i in range(1, 3)}
INSTR = {**ACT, **QST, **NOF}
HELPED = [f"act{i:03d}_1" for i in range(1, 6)]; HARMED = [f"qst{i:03d}_1" for i in range(1, 4)]


def traj(tid, final):
    return [{"step": 0, "code": "x = apis.supervisor.show_account_passwords()", "out": "[{'account_name': 'venmo', ...}]", "resp": "look first"},
            {"step": 1, "code": f"y = len('{tid}')", "out": "Execution successful.", "resp": "compute"},
            {"step": 2, "code": final, "out": "Execution successful.", "resp": "done"}]


def run_json(tag, seed, rows):
    """rows: [(tid, won, final cell)] -> a harness_h1 base log."""
    return {"tag": tag, "seed": seed, "harness_h1": True, "max_steps": 30, "n_games": len(rows), "games": [r[0] for r in rows],
            "won": [r[1] for r in rows], "G": [1.0 if r[1] else 0.5 for r in rows], "crashed": [None] * len(rows), "traj": [traj(r[0], r[2]) for r in rows]}


ANS = "apis.supervisor.complete_task(answer='done')"; NOANS = "apis.supervisor.complete_task()"


def py(*args, env=None):
    r = subprocess.run([sys.executable, os.path.join(HERE, args[0]), *args[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, **(env or {})})
    print(f"$ {' '.join(args)[:160]}\n{r.stdout[-3000:]}")
    assert r.returncode == 0, f"{args[0]} {args[1]} failed ({r.returncode}):\n{r.stderr[-3000:]}"
    return r


def fake_results(build, results):
    """cand arm: action tasks won (act005 only 1 of 2 reps), question tasks lost; none arm: action tasks lost, question tasks won."""
    man = json.load(open(os.path.join(build, "manifest.json"), encoding="utf-8")); n = 0
    for j in man["jobs"]:
        dd = os.path.join(build, j["dir"]); tasks = json.load(open(os.path.join(dd, "tasks.json")))
        rp = json.load(open(os.path.join(dd, f"replay_{j['arm']}.json"))); won, trs = [], []
        for t in tasks:
            q = t.startswith("qst"); w = (not q) if j["arm"] == "cand" else q
            if j["arm"] == "cand" and t == "act005_1" and j["rep"] == 1: w = False
            tr = [{"step": i, "code": c["exec"] if isinstance(c, dict) else c, "out": (c["exec"][7:120] if isinstance(c, dict) else "Execution successful."),
                   "replayed": True, **({"shown": c["shown"][:300]} if isinstance(c, dict) else {})} for i, c in enumerate(rp[t])]
            tr.append({"step": len(tr), "code": NOANS if (j["arm"] == "cand") else ANS, "out": "Execution successful.", "resp": "finish"})
            won.append(w); trs.append(tr)
        json.dump({"tag": j["tag"], "seed": j["seed"], "games": tasks, "won": won, "G": [float(w) for w in won], "crashed": [None] * len(tasks),
                   "traj": trs}, open(os.path.join(results, f"{j['tag']}_seed{j['seed']}.json"), "w")); n += 1
    return n


def main():
    d = tempfile.mkdtemp(prefix="bit_grow_"); res = os.path.join(d, "results"); os.makedirs(res)
    instr = os.path.join(d, "instr.json"); json.dump(INSTR, open(instr, "w"))
    rows1 = [(t, False, ANS) for t in HELPED] + [(t, True, ANS) for t in HARMED] + [(t, True, NOANS) for t in NOF]
    rows2 = [(t, False, ANS) for t in ("act006_1", "act007_1", "act008_1", "act001_1")] + [(t, True, ANS) for t in ("qst004_1", "qst005_1")]
    r1 = os.path.join(res, "SYN_disc_seed1.json"); r2 = os.path.join(res, "SYN_disc_seed2.json")
    json.dump(run_json("SYN_disc", 1, rows1), open(r1, "w")); json.dump(run_json("SYN_disc", 2, rows2), open(r2, "w"))
    envf = os.path.join(d, "base_env.txt"); open(envf, "w").write("BOS_PARSE_UNCLOSED=1 BOS_HARNESS_H1=1\n")
    screen = os.path.join(d, "screen.json"); json.dump({"candidates": [{"cid": "PAR_1", "spec": PARENT}], "kept": ["PAR_1"]}, open(screen, "w"))

    # ---- parent branch build (bit_branch) + fabricated results
    build = os.path.join(d, "branch")
    py("bit_branch.py", "build", "--screen", screen, "--runs", r1, "--instr", instr, "--out", build, "--round", "T0", "--reps", "2", "--env-file", envf,
       "--workers", "2")
    print(f"{fake_results(build, res)} result files fabricated")

    # ---- nodes
    node_p = os.path.join(d, "node.json")
    py("bit_grow.py", "nodes", "--builds", build, "--results", res, "--runs", f"{r1},{r2}", "--instr", instr, "--cid", "PAR_1", "--out", node_p)
    node = json.load(open(node_p, encoding="utf-8")); s = node["stats"]
    assert (s["n"], s["n_helped"], s["n_harmed"], s["n_harmed_logged_won"], s["n_neutral"]) == (8, 5, 3, 3, 0), s
    assert abs(s["sum_d"] - 1.5) < 1e-9 and s["split_eligible"], s
    assert {x["task"] for x in node["states"] if x["group"] == "harmed"} == set(HARMED) and node["parent_spec"]["name"] == PARENT["name"]
    for x in node["states"]:
        assert x["k"] == 2 and x["prefix"]["n_prefix"] == 2 and x["kind"] == "block_once", x
        assert ("cand_won" if x["group"] == "helped" else "cand_lost") in x["refs"], x["refs"]
    print("nodes ok")

    # ---- propose (mock)
    cands = os.path.join(d, "cands_G1.jsonl")
    py("bit_grow.py", "propose", "--node", node_p, "--out", cands, "--run-id", "G1", "--k", "3", "--patch-dir", os.path.join(d, "patches"),
       env={"BOOST_MOCK": "1"})
    r = subprocess.run([sys.executable, os.path.join(HERE, "bit_grow.py"), "propose", "--node", node_p, "--out", cands + ".x", "--run-id", "G1",
                        "--dry-run"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0 and "HARMED states" in r.stdout and "Pending cell" in r.stdout and "Continuation WITH the rule" in r.stdout, r.stderr[-2000:]
    lines = [json.loads(l) for l in open(cands, encoding="utf-8") if l.strip()]
    by = {l["child"]["name"]: l for l in lines}
    import bit_rubric as BR
    for l in lines: assert {"cid", "run", "spec", "valid", "why", "self_check", "patch_path", "raw", "parent_cid"} <= set(l)
    nq = by["task_not_question"]; assert nq["valid"], nq["why"]
    assert len(nq["self_check"]["kept_helped"]) == 5 and nq["self_check"]["kept_neg"] == [], nq["self_check"]
    assert nq["spec"]["kind"] == "block_once" and nq["spec"]["cls"] == PARENT["cls"] and nq["spec"]["note"] == PARENT["note"]
    assert "_bit_parent" in nq["spec"]["detect_src"] and "_bit_child" in nq["spec"]["detect_src"]; BR.validate_spec(nq["spec"])
    assert not by["always_true_child"]["valid"] and by["always_true_child"]["attempts"] == 3, by["always_true_child"]["why"]
    fx = by["no_question_mark_refined"]; assert fx["valid"] and fx["attempts"] == 2 and fx["spec"]["note"] != PARENT["note"], fx
    print("propose ok")

    # ---- evaluate
    ev = os.path.join(d, "eval.json"); child = os.path.join(d, "child.json")
    py("bit_grow.py", "evaluate", "--node", node_p, "--cands", cands, "--out", ev, "--spec-out", child)
    e = json.load(open(ev, encoding="utf-8")); best = e["children"][0]
    assert e["recommended"] == best["cid"] and best["name"] in ("task_not_question", "no_question_mark_refined"), e["recommended"]
    assert abs(best["gain"] - 5.375) < 1e-9, best["gain"]   # 4.5^2/6 + (-3)^2/4 - 1.5^2/9
    assert best["p_pos_kept"] >= 0.9 and best["leaf_kept"] == "intervene" and best["pooled_kept"]["a_bar"] > 0, best
    assert best["n_kept"] == 5 and best["dropped_harmed"] == 3 and best["dropped_helped"] == 0 and abs(best["value_removed"] - 3.0) < 1e-9, best
    assert {x["task"] for x in node["states"] if x["sid"] in best["dropped"]} == set(HARMED)
    assert os.path.exists(child)
    print(f"evaluate ok: gain {best['gain']:.3f}, P(a_kept>0) {best['p_pos_kept']:.3f}, value removed {best['value_removed']:+.1f}")

    # ---- heldout: seed-2 states outside the node (act006-008 + the new act001 episode; question tasks never fire)
    for flag, want in (([], {"act006_1", "act007_1", "act008_1", "act001_1"}), (["--exclude-node-tasks"], {"act006_1", "act007_1", "act008_1"})):
        out = os.path.join(d, "heldout" + ("_nt" if flag else ""))
        py("bit_grow.py", "heldout", "--child-spec", child, "--runs", f"{r1},{r2}", "--instr", instr, "--exclude-eids", node_p, "--out", out,
           "--round", "T0H", "--env-file", envf, "--reps", "2", "--workers", "2", *flag)
        man = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8")); got = {}
        for c in man["cands"]:
            for dd in c["dirs"]: got.update(json.load(open(os.path.join(out, dd["dir"], "meta.json"), encoding="utf-8")))
        assert set(got) == want, sorted(got)
        assert all(m["eid"].startswith("SYN_disc_s2:") for m in got.values()) and not ({m["eid"] for m in got.values()} & {x["eid"] for x in node["states"]})
        jobs = [l for l in open(os.path.join(out, "jobs.txt"), encoding="utf-8").read().splitlines() if l.strip()]
        assert len(jobs) == 4 and all("CC_BIT_T0H_" in j for j in jobs), jobs   # 1 seed dir x 2 arms x 2 reps
    print("heldout ok")
    print(f"BIT GROW TEST OK  {d}")


if __name__ == "__main__":
    main()
