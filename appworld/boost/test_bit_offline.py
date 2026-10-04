"""BIT offline end-to-end test (docs/design/BIT_IMPLEMENTATION_PLAN.md Unit G): B (bit_tree) -> D (bit_propose, BOOST_MOCK=1) -> E (bit_screen)
-> G (bit_bench_d10) -> F build (bit_branch) on the local H1 disc logs. No server, no AppWorld, no LLM. Stages whose module is absent are
skipped with a message; a synthetic cands JSONL (Unit D schema: a D10 copy, the null note, an always-step-0 note, a '?' note) is always
added so E / G / F are exercised without the proposer.
Asserts: tree interface, D10_ref fidelity on H1 disc s1 (4/8 losses = e7f15ba, 4242c97, d9987f6, 77bcb81; 0/42 wins), the frozen gold set,
cands / screen.json / branch manifest interfaces, and the rediscovery sanity (D10_ref passes, null_note fails).
usage (from the repo root): py appworld/boost/test_bit_offline.py      data dir: $BIT_CCD (default = the local scratchpad ccdata)"""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bit_bench_d10 as G   # noqa: E402  (G.CCD honours $BIT_CCD)

CCD = G.CCD; RUNS = [os.path.join(CCD, f"CC_H1_F0_disc_seed{s}.json") for s in (1, 2)]; INSTR = os.path.join(CCD, "instructions_all100.json")
REFS = os.path.join(HERE, "bit_refs"); D10 = os.path.join(REFS, "D10_ref.json"); NULL = os.path.join(REFS, "null_note.json")
S1_GOLD = {f"CC_H1_F0_disc_s1:{t}" for t in ("e7f15ba_1", "4242c97_1", "d9987f6_1", "77bcb81_1")}
CAND_KEYS = {"cid", "run", "case_id", "task", "spec", "valid", "why", "self_check", "patch_path", "usage", "raw"}
SPEC_KEYS = {"name", "kind", "cls", "hypothesis", "note", "detect_src", "origin"}


def py(script, *args, env=None, check=True):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**os.environ, **(env or {})})
    print(f"$ {script} {' '.join(args)[:200]}\n{r.stdout[-2500:]}")
    if check: assert r.returncode == 0, f"{script} failed ({r.returncode}):\n{r.stderr[-3000:]}"
    return r


def synth_cands(path, tree, run="SYN"):
    """Unit D-shaped lines: D10 rediscovered by a 'proposer' (positive control for the bench), plus three negative / null controls."""
    gold = set(json.load(open(G.DEF_GOLD, encoding="utf-8"))["gold"])
    gcase = next((c for c in tree["cases"] if c["lost"] in gold), tree["cases"][0])
    other = next((c for c in tree["cases"] if c["lost"] not in gold), tree["cases"][-1])
    d10 = json.load(open(D10, encoding="utf-8")); d10.pop("ref", None); d10["name"] = "syn_answer_on_action_task"
    nul = json.load(open(NULL, encoding="utf-8")); nul.pop("ref", None); nul["name"] = "syn_null_step5"
    step0 = {"name": "syn_always_step0", "kind": "note", "cls": "control_flow", "hypothesis": "always fires at step 0 (screening control)",
             "note": "Read the whole task carefully and plan all the API calls you will need before writing code.",
             "detect_src": "def detect(view):\n    return view[\"step\"] == 0\n"}
    qmark = {"name": "syn_question_mark", "kind": "note", "cls": "task_knowledge", "hypothesis": "fires on question tasks (screening control)",
             "note": "This task asks a question: pass the requested value as the answer argument of complete_task.",
             "detect_src": "def detect(view):\n    return \"?\" in (view[\"task\"] or \"\")\n"}
    lines = []
    for j, (sp, case) in enumerate(((d10, gcase), (nul, other), (step0, other), (qmark, other))):
        sp["origin"] = {"case_id": case["case_id"], "run": run}
        lines.append({"cid": f"{run}_{case['case_id']}_{j}", "run": run, "case_id": case["case_id"], "task": case["task"], "spec": sp,
                      "valid": True, "why": "", "self_check": {"fires_lost": None, "k_lost": None, "fires_won": None},
                      "patch_path": None, "usage": {}, "raw": ""})
    with open(path, "w", encoding="utf-8") as f:
        for l in lines: f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return gcase


def main():
    import bit_common as BC, bit_tree as BT, bit_rubric as BR
    assert all(os.path.exists(p) for p in RUNS + [INSTR]), f"missing local data in {CCD} (set BIT_CCD)"
    d = tempfile.mkdtemp(prefix="bit_offline_"); runs = ",".join(RUNS); skipped = []
    eps = [e for e in BC.load_episodes(RUNS, INSTR) if not e["crashed"]]
    n_won = sum(e["won"] for e in eps); print(f"{len(eps)} H1 disc episodes ({n_won} won) from {CCD}")

    # ---- B: memory tree
    full = BT.build_tree(eps, RUNS, top=1000, max_per_task=1000)
    assert {"runs", "episodes", "tasks", "nodes", "cases"} <= set(full)
    roots = [n for n in full["nodes"] if n["depth"] == 0]
    assert sum(n["n_win"] for n in roots) == n_won, "root wins != total wins"
    assert {c["lost"] for c in full["cases"]} == {e["eid"] for e in eps if not e["won"]}, "a loss is missing from the cases"
    tree_p = os.path.join(d, "tree.json"); py("bit_tree.py", "--runs", runs, "--instr", INSTR, "--out", tree_p)
    tree = json.load(open(tree_p, encoding="utf-8"))
    assert all(set(c) >= {"case_id", "task", "lost", "won", "fork_depth", "priority"} for c in tree["cases"]) and tree["cases"]
    print(f"B ok: {len(full['cases'])} losses = cases, {len(tree['cases'])} top cases")

    # ---- C fidelity: D10_ref on H1 disc s1 = 4/8 losses, 0/42 wins (last-step rule: b6d1f70 excluded)
    s1 = [e for e in eps if e["seed"] == 1]
    res = BR.simulate(BR.compile_patch([json.load(open(D10, encoding="utf-8"))]), s1)
    fl = {e["eid"] for e in s1 if res[e["eid"]]["fires"] and not e["won"]}; fw = {e["eid"] for e in s1 if res[e["eid"]]["fires"] and e["won"]}
    nl = sum(not e["won"] for e in s1); nw = len(s1) - nl
    print(f"C fidelity: D10_ref fires on {len(fl)}/{nl} losses, {len(fw)}/{nw} wins")
    assert (len(fl), nl, len(fw), nw) == (4, 8, 0, 42) and fl == S1_GOLD, (sorted(fl), sorted(fw))

    # ---- gold set frozen and reproducible
    gold = json.load(open(G.DEF_GOLD, encoding="utf-8")); g2 = G.build_gold(RUNS, INSTR)
    assert g2["gold"] == gold["gold"] and g2["final_k"] == gold["final_k"], "gold set no longer reproduces from the logs"
    assert {e for e in gold["gold"] if e.startswith("CC_H1_F0_disc_s1:")} == S1_GOLD and gold["cross_check"]["agree"]
    print(f"gold ok: {len(gold['gold'])} episodes")

    # ---- D: proposer (mock)
    cand_files = []; syn = os.path.join(d, "cands_SYN.jsonl"); synth_cands(syn, tree)
    if os.path.exists(os.path.join(HERE, "bit_propose.py")):
        cp = os.path.join(d, "cands_P0.jsonl")
        py("bit_propose.py", "--tree", tree_p, "--runs", runs, "--instr", INSTR, "--out", cp, "--run-id", "P0", "--n-cases", "3",
           "--k-per-case", "2", "--workers", "2", "--patch-dir", os.path.join(d, "patches"), env={"BOOST_MOCK": "1"})
        lines = [json.loads(l) for l in open(cp, encoding="utf-8") if l.strip()]
        assert lines, "bit_propose wrote no lines"
        for l in lines:
            assert CAND_KEYS <= set(l), f"cands line keys: missing {CAND_KEYS - set(l)}"
            assert set(l["self_check"]) >= {"fires_lost", "k_lost", "fires_won"}
            if l["valid"]: assert SPEC_KEYS <= set(l["spec"]) and l["spec"]["kind"] in BR.KINDS; BR.validate_spec(l["spec"])
        print(f"D ok: {len(lines)} lines, {sum(bool(l['valid']) for l in lines)} valid")
        cand_files.append(cp)
    else:
        skipped.append("D"); print("D SKIPPED: boost/bit_propose.py not found (synthetic cands only)")
    cand_files.append(syn)

    # ---- E: screening
    screen_p = None
    if os.path.exists(os.path.join(HERE, "bit_screen.py")):
        screen_p = os.path.join(d, "screen.json")
        py("bit_screen.py", "--cands", ",".join(cand_files), "--runs", runs, "--instr", INSTR, "--tree", tree_p, "--out", screen_p,
           "--refs", f"{D10},{NULL}", "--workers", "4")
        sc = json.load(open(screen_p, encoding="utf-8"))
        assert {"params", "candidates", "kept"} <= set(sc)
        byname = {c["name"]: c for c in sc["candidates"]}; cids = {c["cid"] for c in sc["candidates"]}
        assert all(k in cids for k in sc["kept"]) and not any(c.get("ref") and c["cid"] in sc["kept"] for c in sc["candidates"])
        ok = [c for c in sc["candidates"] if not c.get("error")]
        for c in ok: assert {"cid", "gain_within", "gain_raw", "n_fire", "ic", "dir"} <= set(c), set(c)
        ref = next(c for c in sc["candidates"] if c.get("ref") and c["name"] == "d10_answer_on_action_task")
        top_raw = max(c["gain_raw"] for c in ok)
        print(f"E: D10_ref gain_raw {ref['gain_raw']:.3f} (max {top_raw:.3f}), ic {ref['ic']:+.3f}; step0 gain_within "
              f"{byname['syn_always_step0']['gain_within']}; '?' dir {byname['syn_question_mark']['dir']}; kept {sc['kept']}")
        assert ref["ic"] > 0 and ref["gain_within"] > 0, "D10_ref must have a positive IC and gain_within"
        assert byname["syn_always_step0"]["gain_within"] == 0, "always-step-0 must get gain_within = 0"
        # plan-level expectations of Unit E that depend on its gain definitions / the data, reported but not fatal
        top_val = max(c["value"] for c in ok)
        assert ref["value"] >= top_val - 1e-9, f"D10_ref value {ref['value']} is not the top ({top_val})"   # gain_raw grows with coverage; value is the keep score
        print(f"E: D10_ref value {ref['value']:.2f} = top")
        if byname["syn_question_mark"]["dir"] >= 0: print(f"E WARN: '?' candidate dir = {byname['syn_question_mark']['dir']} (plan: < 0)")
        print("E ok")
    else:
        skipped.append("E"); print("E SKIPPED: boost/bit_screen.py not found")

    # ---- G: rediscovery bench
    bench_p = os.path.join(d, "bench.json")
    args = ["bench", "--cands", ",".join(cand_files), "--tree", tree_p, "--runs", runs, "--instr", INSTR, "--out", bench_p, "--workers", "4"]
    py("bit_bench_d10.py", *(args + (["--screen", screen_p] if screen_p else [])))
    b = json.load(open(bench_p, encoding="utf-8"))
    assert b["sanity"]["ok"], f"sanity: {b['sanity']}"
    s = b["runs"]["SYN"]; rd = s["rediscovery"]
    assert s["exposure"] >= 1 and rd["any_valid"] and s["best"]["name"] == "syn_answer_on_action_task", s
    assert s["candidates"][next(c for c, v in s["candidates"].items() if v["name"] == "syn_null_step5")]["passes"] is False
    for k in ("exposure", "rediscovery", "best", "n_valid"): assert all(k in r for r in b["runs"].values())
    print(f"G ok: sanity {b['sanity']['ok']}; SYN exposure {s['exposure']} any={rd['any_valid']} kept={rd['screen_kept']} "
          f"top1_within={(rd['top1_gain_within'] or {}).get('passes')} top1_raw={(rd['top1_gain_raw'] or {}).get('passes')}")

    # ---- F: branch-at-fire build
    if os.path.exists(os.path.join(HERE, "bit_branch.py")) and screen_p:
        envf = os.path.join(d, "base_env.txt")
        open(envf, "w", encoding="utf-8").write("BOS_PARSE_UNCLOSED=1 BOS_HARNESS_H1=1 BOS_AW_INSTR=prompts/instructions_h1.txt\n")
        out = os.path.join(d, "branch")
        py("bit_branch.py", "build", "--screen", screen_p, "--cands", ",".join(cand_files), "--runs", runs, "--instr", INSTR, "--out", out,
           "--round", "R0", "--env-file", envf, "--refs", D10, "--force-cid", "ref_d10_answer_on_action_task", "--workers", "4")
        man = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8")); jobs = open(os.path.join(out, "jobs.txt"), encoding="utf-8").read().split("\n")
        jobs = [j for j in jobs if j.strip()]
        assert man.get("jobs") and jobs and all("CC_BIT_R0" in j for j in jobs), "manifest / jobs.txt"
        for j in man["jobs"]:
            dd = os.path.join(out, j["dir"])
            assert all(os.path.exists(os.path.join(dd, f)) for f in ("tasks.json", "replay_none.json", "replay_cand.json", "meta.json")), dd
        blk = [j for j in man["jobs"] if "d10" in j["cid"].lower()]
        if blk:   # block_once replay: cand = codes[:k] + [{"exec", "shown"}], none = codes[:k+1]
            dd = os.path.join(out, blk[0]["dir"]); rc = json.load(open(os.path.join(dd, "replay_cand.json"), encoding="utf-8"))
            rn = json.load(open(os.path.join(dd, "replay_none.json"), encoding="utf-8")); t = next(iter(rc))
            assert isinstance(rc[t][-1], dict) and set(rc[t][-1]) == {"exec", "shown"} and rc[t][-1]["shown"] == rn[t][-1]
            assert len(rc[t]) == len(rn[t]) and rc[t][:-1] == rn[t][:-1]
        print(f"F ok: {len(jobs)} jobs, {len(man['jobs'])} manifest jobs")
    else:
        skipped.append("F"); print("F SKIPPED: boost/bit_branch.py not found" if screen_p else "F SKIPPED: needs screen.json (E)")

    print(f"BIT OFFLINE TEST OK{' (skipped: ' + ','.join(skipped) + ')' if skipped else ''}  {d}")


if __name__ == "__main__":
    main()
