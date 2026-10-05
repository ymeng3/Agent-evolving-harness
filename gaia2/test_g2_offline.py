"""Gaia2 BIT offline end-to-end test (docs/design/GAIA2_ADAPTER_PLAN.md U6). No ARE, no server, no LLM.
A synthetic Gaia2 result fixture (plan section 2 result schema: 2 seeds x 6 scenarios, mixed outcomes, a crashed episode, no_exec steps,
notifications appended after the exec output, rationale / rationale_diag) goes through bit_common.load_episodes -> bit_tree ->
bit_rubric.simulate(gaia2/bit_refs) -> g2_failed_checks -> bit_propose (BOOST_MOCK=1, --bench gaia2) -> bit_screen -> bit_branch build
(--harness-cmd <are-env python> ../gaia2/bos_gaia2.py) -> bit_active tasks (--harness-cmd), then re-runs appworld/boost/test_bit_offline.py
to confirm the AppWorld path is unchanged.
usage (from the repo root): py gaia2/test_g2_offline.py [--skip-appworld]"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); BOOST = os.path.join(os.path.dirname(HERE), "appworld", "boost")
sys.path.insert(0, BOOST); sys.path.insert(0, HERE)
REFS = os.path.join(HERE, "bit_refs"); NULL3 = os.path.join(REFS, "null_note_step3.json"); SBW = os.path.join(REFS, "send_before_write.json")
G2_CMD = "env -u PYTHONPATH /root/autodl-tmp/cc/are-env/bin/python ../gaia2/bos_gaia2.py"
TIDS = ["g2_exec_001", "g2_exec_002", "g2_multi_003", "g2_search_004", "g2_time_005", "g2_ambig_006"]
CONFIGS = ["execution", "execution", "adaptability", "search", "time", "ambiguity"]
INSTR = {"g2_exec_001": "Schedule a 30 minute call with Ann Lee tomorrow at 10am.",
         "g2_exec_002": "Add a lunch with Bob Stone on Friday at noon to my calendar.",
         "g2_multi_003": "Email Carla Diaz the agenda for Monday's meeting.",
         "g2_search_004": "How many unread emails do I have from Dan Wu?",
         "g2_time_005": "In two minutes, when Eve replies, add her suggested slot to my calendar.",
         "g2_ambig_006": "Book the usual for Saturday."}


# ---------------------------------------------------------------- fixture
def step(k, code, out, t, err=False, no_exec=False, notif=""):
    """one traj step with the plan's per-step keys (out[:200], resp[-600:], ...); notifications follow the exec output."""
    full = out + (("\n" + notif) if notif else "")
    return {"step": k, "code": "" if no_exec else code, "out": ("" if no_exec else full)[:200],
            "resp": ("I will look at the apps first.\n```python\n" + code + "\n```")[-600:] if not no_exec else "Let me think about the request.",
            "exec_error": bool(err), "replayed": False, "no_exec": bool(no_exec), "code_final": ("" if no_exec else code)[:300], "free_retries": 0,
            "t_sim": float(t), "notif": notif[:300], "calls": [] if no_exec else re.findall(r"\b[A-Z]\w*__\w+(?=\s*\()", code),
            "writes": 0 if no_exec else len(re.findall(r"__(?:add|send_email|send_message\b|create)", code)), "pc": k == 0, "gp": None, "gf": None}


COUNTS = ("Failure: \nAgent and oracle counters do not match for the following tools:\n"
          "- Tool 'Calendar__add_calendar_event': Agent count 0, Oracle count 1")
ORACLE_MAIL = ("Failure: Agent did not perform the following oracle tool call:\ntool name: EmailClientV2__send_email\ntool args:\n"
               "-recipients: ['carla.diaz@example.com']\n-subject: Agenda for Monday\n-content: 1. budget 2. hiring\n\nList of matching attempts:\n")
ORACLE_REPLY = ("Failure: Agent did not perform the following oracle tool call:\ntool name: AgentUserInterface__send_message_to_user\ntool args:\n"
                "-content: You have 3 unread emails from Dan Wu.\n\nList of matching attempts:\n"
                "-Failure matching agent event (ID: Agent-1) with oracle event (ID: Oracle-7), reason: tool judge reject")
N1 = "[2024-10-15 09:00:03] New email from it-desk@example.com: Password expires soon"


def ep_write_first(won=True):
    """write, then reply (send_before_write must not fire); step 1 is a no_exec step."""
    tr = [step(0, 'r = Contacts__search_contacts(query="Ann")\nprint(r)', "[{'id': 'c1', 'first_name': 'Ann', 'last_name': 'Lee'}]", 1),
          step(1, "", "", 2, no_exec=True),
          step(2, 'print(Calendar__add_calendar_event(title="Call with Ann", start_datetime="2024-10-16 10:00:00", end_datetime="2024-10-16 10:30:00"))',
               "evt_91f2", 3, notif=N1),
          step(3, 'AgentUserInterface__send_message_to_user(content="I scheduled the call.")', "None", 4)]
    return tr, won, 1.0 if won else 0.5, ("" if won else COUNTS), None, "turns_done", 1, 1


def ep_reply_first():
    """reads only, then the reply (send_before_write fires at k=3, after the no_exec step 1)."""
    tr = [step(0, 'r = Contacts__search_contacts(query="Bob")\nprint(r)', "[{'id': 'c2', 'first_name': 'Bob', 'last_name': 'Stone'}]", 1),
          step(1, "", "", 2, no_exec=True),
          step(2, 'print(Calendar__get_calendar_events_from_to(start_datetime="2024-10-18 00:00:00", end_datetime="2024-10-19 00:00:00"))',
               "{'events': []}", 3, notif=N1),
          step(3, 'AgentUserInterface__send_message_to_user(content="Your lunch is in the calendar.")', "None", 4)]
    return tr, False, 0.0, COUNTS, None, "turns_done", 1, 1


def ep_loop_fail():
    """the same failing write call 3 times, a no_exec step, then the budget/time runs out before the reply (multi-turn scenario)."""
    bad = 'EmailClientV2__send_email(to="carla.diaz@example.com", text="agenda")'
    msg = ("Execution failed. Traceback (most recent call last):\n  File \"<cell>\", line 1\nTypeError: send_email() got an unexpected keyword "
           "argument 'to'\n[harness] Signature (* = required): EmailClientV2__send_email(recipients:list*, subject:str, content:str)")
    tr = [step(0, 'print(Contacts__search_contacts(query="Carla"))', "[{'id': 'c3', 'first_name': 'Carla'}]", 1),
          step(1, bad, msg, 2, err=True, notif=N1), step(2, bad, msg, 3, err=True), step(3, bad, msg, 4, err=True),
          step(4, "", "", 5, no_exec=True)]
    return tr, False, 0.0, "Validation called at turn 0 but nb_turns is 2", ORACLE_MAIL, "time_up", 2, 0


def ep_mail_ok():
    tr = [step(0, 'print(Contacts__search_contacts(query="Carla"))', "[{'id': 'c3', 'first_name': 'Carla'}]", 1),
          step(1, 'print(EmailClientV2__send_email(recipients=["carla.diaz@example.com"], subject="Agenda", content="1. budget"))', "mail_77", 2),
          step(2, 'AgentUserInterface__send_message_to_user(content="Sent.")', "None", 3,
               notif="[user message] Thanks! Please also add it to my calendar."),
          step(3, 'print(Calendar__add_calendar_event(title="Meeting", start_datetime="2024-10-21 09:00:00", end_datetime="2024-10-21 10:00:00"))',
               "evt_12", 64),
          step(4, 'AgentUserInterface__send_message_to_user(content="Added to your calendar.")', "None", 65)]
    return tr, True, 1.0, "", None, "turns_done", 2, 2


def ep_search(won):
    tr = [step(0, 'm = EmailClientV2__list_emails(folder_name="INBOX", offset=0, limit=50)\nprint(len(m))', "50", 1),
          step(1, 'print(sum(1 for e in m if e.sender == "dan.wu@example.com" and not e.is_read))', "3" if won else "2", 2),
          step(2, f'AgentUserInterface__send_message_to_user(content="You have {3 if won else 2} unread emails from Dan Wu.")', "None", 3)]
    return tr, won, 1.0, ("" if won else ORACLE_REPLY), None, "turns_done", 1, 1


def ep_time():
    tr = [step(0, 'print(SystemApp__wait_for_notification(timeout=180))', "None", 121,
               notif="[2024-10-15 09:02:01] New message from Eve: Thursday 3pm works"),
          step(1, 'print(Calendar__add_calendar_event(title="Eve", start_datetime="2024-10-17 15:00:00", end_datetime="2024-10-17 16:00:00"))',
               "evt_5", 122),
          step(2, 'AgentUserInterface__send_message_to_user(content="Added Thursday 3pm with Eve.")', "None", 123)]
    return tr, True, 1.0, "", None, "turns_done", 1, 1


def ep_crashed():
    return [], False, None, None, None, "crashed", 1, 0


PLAN = {1: [ep_reply_first, ep_write_first, ep_loop_fail, lambda: ep_search(True), ep_time, ep_crashed],
        2: [ep_write_first, ep_reply_first, ep_mail_ok, lambda: ep_search(False), ep_time, ep_reply_first]}


def fixture(seed, tag="G2T_disc"):
    d = {"tag": tag, "seed": seed, "bench": "gaia2", "harness_v2": True, "harness_h1": True, "harness_h11": True, "no_eval": True,
         "max_steps": 40, "gen_seconds": 1.0, "think": False, "judge_model": "qwen/qwen3.8-27b", "judge_hits": 3, "judge_misses": 9,
         "games": [], "won": [], "traj": [], "crashed": [], "G": [], "configs": [], "instr": [], "rationale": [], "rationale_diag": [],
         "end_reason": [], "nb_turns": [], "turns_done": [], "state_hash": [], "agent_counts": [], "oracle_counts": [], "fired": []}
    for t, cfg, mk in zip(TIDS, CONFIGS, PLAN[seed]):
        tr, won, G, rat, diag, er, nt, td = mk()
        for k, v in (("games", t), ("won", won), ("traj", tr), ("crashed", er == "crashed"), ("G", G), ("configs", cfg), ("instr", INSTR[t]),
                     ("rationale", rat), ("rationale_diag", diag), ("end_reason", er), ("nb_turns", nt), ("turns_done", td),
                     ("state_hash", f"{abs(hash((t, seed))) % 16 ** 12:012x}"), ("agent_counts", {}), ("oracle_counts", {}), ("fired", [])):
            d[k].append(v)
    return d


# ---------------------------------------------------------------- helpers
def py(script, *args, env=None, check=True):
    path = script if os.path.isabs(script) else os.path.join(BOOST if script.startswith("bit_") else HERE, script)
    r = subprocess.run([sys.executable, path, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, **(env or {})})
    print(f"$ {os.path.basename(path)} {' '.join(args)[:200]}\n{r.stdout[-2000:]}")
    if check: assert r.returncode == 0, f"{script} failed ({r.returncode}):\n{r.stderr[-3000:]}"
    return r


def main():
    import bit_common as BC, bit_rubric as BR, bit_branch as BB
    d = tempfile.mkdtemp(prefix="g2_offline_"); rdir = os.path.join(d, "results"); os.makedirs(rdir)
    runs = []
    for s in (1, 2):
        p = os.path.join(rdir, f"G2T_disc_seed{s}.json"); json.dump(fixture(s), open(p, "w", encoding="utf-8"), indent=1); runs.append(p)
    RUNS = ",".join(runs); instr_p = os.path.join(d, "instr_empty.json"); json.dump({}, open(instr_p, "w"))

    # ---- A: episodes (bench, instr fallback to the run's own list, Gaia2 per-episode fields)
    all_eps = BC.load_episodes(runs, instr_p); eps = [e for e in all_eps if not e["crashed"]]
    assert len(all_eps) == 12 and len(eps) == 11 and all(e["bench"] == "gaia2" and e["max_steps"] == 40 for e in all_eps)
    assert all(e["instr"] == INSTR[e["task"]] for e in all_eps), "instr must fall back to d['instr'][i]"
    e0 = next(e for e in eps if e["eid"] == "G2T_disc_s1:g2_multi_003")
    assert e0["end_reason"] == "time_up" and e0["nb_turns"] == 2 and e0["turns_done"] == 0 and e0["rationale_diag"] == ORACLE_MAIL
    e1 = next(e for e in eps if e["eid"] == "G2T_disc_s1:g2_exec_002")
    assert e0["steps"][1]["err"] and e1["steps"][2]["out"] == "evt_91f2\n" + N1, "error prefix kept, notification after the output"
    assert any(s["no_exec"] and s["code"] == "" for e in eps for s in e["steps"])
    assert BR._prompt_proxy(e0, 0) == f"Current time: (t)\nTask: {INSTR['g2_multi_003']}"
    assert BR._prompt_proxy(e0, 2).endswith("[2 of 40 steps used]")
    print(f"A ok: {len(all_eps)} episodes ({sum(e['won'] for e in eps)} won, 1 crashed)")

    # ---- B: memory tree
    tree_p = os.path.join(d, "tree.json"); py("bit_tree.py", "--runs", RUNS, "--instr", instr_p, "--out", tree_p)
    tree = json.load(open(tree_p, encoding="utf-8"))
    assert {c["lost"] for c in tree["cases"]} == {e["eid"] for e in eps if not e["won"]} and any(c["won"] for c in tree["cases"])
    print(f"B ok: {len(tree['cases'])} cases")

    # ---- C: simulate the refs + the gaia2 pre_complete marker
    res = BR.simulate(BR.compile_patch([json.load(open(NULL3, encoding="utf-8"))], 40), eps)
    for e in eps:
        f = res[e["eid"]]["fires"]
        assert ([x["k"] for x in f] == [3]) == (len(e["steps"]) > 3), (e["eid"], f)
    res = BR.simulate(BR.compile_patch([json.load(open(SBW, encoding="utf-8"))], 40), eps)
    fired = {eid: r["fires"][0]["k"] for eid, r in res.items() if r["fires"]}
    want = {"G2T_disc_s1:g2_exec_001": 3, "G2T_disc_s2:g2_exec_002": 3, "G2T_disc_s2:g2_ambig_006": 3,
            "G2T_disc_s1:g2_search_004": 2, "G2T_disc_s2:g2_search_004": 2}
    assert fired == want, fired
    assert all(r["hook_errors"] == 0 for r in res.values())
    pc = ('EDITS = [{"id": "e1", "capability": "Verification", "impl": "ControlFlow", "trigger": "t", "depends": []}]\n\n\n'
          'def e1_pre_complete(code, state):\n    return "print(1)"\n')
    r1 = BR.simulate(pc, eps, timeout_s=None); r2 = BR.simulate(pc, [{**e, "bench": "appworld"} for e in eps], timeout_s=None)
    first_send = {e["eid"]: next((s["k"] for s in e["steps"] if "send_message_to_user" in s["code"]), None) for e in eps}
    assert {k: (v["fires"][0]["k"] if v["fires"] else None) for k, v in r1.items()} == first_send, "pre_complete must trigger on send_message_to_user"
    assert not any(v["fires"] for v in r2.values()), "AppWorld episodes keep the complete_task marker"
    print(f"C ok: null_note_step3 at k=3, send_before_write fires {sorted(fired)}, pre_complete marker ok")

    # ---- privileged verifier lines
    ft_p = os.path.join(d, "failed_checks.json"); py("g2_failed_checks.py", "--tree", tree_p, "--runs", RUNS, "--out", ft_p)
    ft = json.load(open(ft_p, encoding="utf-8"))
    assert set(ft) == {c["lost"] for c in tree["cases"]}
    assert ft["G2T_disc_s1:g2_exec_001"] == ["write calls of Calendar__add_calendar_event: agent 0, oracle 1"], ft
    assert ft["G2T_disc_s1:g2_multi_003"] == ["the episode ended before its last turn (validation at turn 0 of 2)",
                                              "oracle action EmailClientV2__send_email not matched (no agent call of this tool to match)"], ft
    assert ft["G2T_disc_s2:g2_search_004"] == ["oracle action AgentUserInterface__send_message_to_user not matched (agent calls tried: tool judge reject)"]
    assert "carla" not in json.dumps(ft).lower() and "3 unread" not in json.dumps(ft), "default lines must not carry oracle args"
    fa_p = os.path.join(d, "failed_checks_args.json"); py("g2_failed_checks.py", "--tree", tree_p, "--runs", RUNS, "--out", fa_p, "--with-args")
    fa = json.load(open(fa_p, encoding="utf-8"))
    assert "  arg recipients = ['carla.diaz@example.com']" in fa["G2T_disc_s1:g2_multi_003"], fa
    print("failed_checks ok")

    # ---- D: proposer prompt (--bench auto -> gaia2) and mock run (--bench gaia2)
    r = py("bit_propose.py", "--tree", tree_p, "--runs", RUNS, "--instr", instr_p, "--out", os.path.join(d, "x.jsonl"), "--run-id", "G0",
           "--failed-tests", ft_p, "--dry-run")
    P = r.stdout
    for s in ("Gaia2", "App__tool(arg=...)", "AgentUserInterface__send_message_to_user", "SystemApp__wait_for_notification",
              "Verifier rationale (privileged", "write-action overlap with the oracle (1 = same counts)", "end_reason = ", "turn(s) done",
              '"max_steps": 40', "help('App__tool')"):
        assert s in P, f"proposer prompt lacks {s!r}"
    example = P.split("Format example", 1)[1]
    assert "send_message" not in example and "answer" not in example.lower() and "complete_task" not in P and "apis." not in P
    cp = os.path.join(d, "cands_G0.jsonl")
    py("bit_propose.py", "--tree", tree_p, "--runs", RUNS, "--instr", instr_p, "--out", cp, "--run-id", "G0", "--n-cases", "4", "--k-per-case", "2",
       "--workers", "2", "--bench", "gaia2", "--failed-tests", ft_p, "--patch-dir", os.path.join(d, "patches"), env={"BOOST_MOCK": "1"})
    lines = [json.loads(l) for l in open(cp, encoding="utf-8") if l.strip()]
    assert lines and all({"cid", "spec", "valid", "why", "self_check"} <= set(l) for l in lines)
    print(f"D ok: {len(lines)} lines, {sum(bool(l['valid']) for l in lines)} valid")

    # synthetic candidates (always present, so E / F do not depend on the mock)
    syn = os.path.join(d, "cands_SYN.jsonl"); case = tree["cases"][0]
    sbw = json.load(open(SBW, encoding="utf-8")); sbw.pop("ref", None); sbw["name"] = "syn_send_before_write"
    step0 = {"name": "syn_always_step0", "kind": "note", "cls": "control_flow", "hypothesis": "always fires at step 0 (screening control)",
             "note": "Read the request carefully and list the apps and tools you will need before writing code.",
             "detect_src": "def detect(view):\n    return view[\"step\"] == 0\n"}
    with open(syn, "w", encoding="utf-8") as f:
        for j, sp in enumerate((sbw, step0)):
            sp["origin"] = {"case_id": case["case_id"], "run": "SYN"}
            f.write(json.dumps({"cid": f"SYN_{case['case_id']}_{j}", "run": "SYN", "case_id": case["case_id"], "task": case["task"], "spec": sp,
                                "valid": True, "why": "", "self_check": {}, "patch_path": None, "usage": {}, "raw": ""}) + "\n")

    # ---- E: screening
    screen_p = os.path.join(d, "screen.json")
    py("bit_screen.py", "--cands", f"{cp},{syn}", "--runs", RUNS, "--instr", instr_p, "--tree", tree_p, "--out", screen_p,
       "--refs", f"{NULL3},{SBW}", "--workers", "2")
    sc = json.load(open(screen_p, encoding="utf-8")); byname = {c["name"]: c for c in sc["candidates"]}
    assert sc["params"]["max_steps"] == 40 and sc["params"]["n_episodes"] == 11
    assert byname["send_before_write"]["ref"] and byname["send_before_write"]["n_fire"] == 5 and byname["syn_always_step0"]["gain_within"] == 0
    print(f"E ok: kept {sc['kept']}")

    # ---- F: branch-at-fire build with the Gaia2 harness command
    envf = os.path.join(d, "g2_env.txt"); open(envf, "w").write("G2_STEPS=40 G2_GEN_SECONDS=1.0 BOS_THINK_OFF=1 PYTHONHASHSEED=0\n")
    out = os.path.join(d, "branch")
    py("bit_branch.py", "build", "--screen", screen_p, "--cands", f"{cp},{syn}", "--runs", RUNS, "--instr", instr_p, "--out", out, "--round", "G0",
       "--env-file", envf, "--refs", f"{NULL3},{SBW}", "--force-cid", "ref_send_before_write", "--force-cid", "ref_null_note_step3",
       "--harness-cmd", G2_CMD, "--workers", "4")
    man = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8"))
    jobs = [j for j in open(os.path.join(out, "jobs.txt"), encoding="utf-8").read().split("\n") if j.strip()]
    assert jobs and len(jobs) == len(man["jobs"]) and man["max_steps"] == 40
    for j in jobs:
        assert f"{G2_CMD} eval --patch " in j and "bos_appworld_v3" not in j and " cd " not in j and "G2_STEPS=40" in j, j
    items = []
    for c in man["cands"]:
        for dd in c["dirs"]:
            rc = json.load(open(os.path.join(out, dd["dir"], "replay_cand.json"), encoding="utf-8"))
            rn = json.load(open(os.path.join(out, dd["dir"], "replay_none.json"), encoding="utf-8"))
            for t in rc:
                items += rc[t] + rn[t]
                if c["kind"] == "block_once":
                    assert isinstance(rc[t][-1], dict) and set(rc[t][-1]) == {"exec", "shown"} and rc[t][-1]["shown"] == rn[t][-1]
                    assert "send_message_to_user" in rn[t][-1] and rc[t][:-1] == rn[t][:-1]
    assert "" in items, "replay files must keep no_exec steps as \"\" items"
    assert any(isinstance(x, dict) for x in items), "block_once cand replay must contain a dict item"
    print(f"F ok: {len(jobs)} jobs; {sum(1 for x in items if x == '')} \"\" items, {sum(1 for x in items if isinstance(x, dict))} dict items")

    # ---- harness command plumbing of valarm / bit_active (valarm itself writes into appworld/patches_ccbit, so only its helper is run)
    class A: harness_cmd = G2_CMD
    assert " ".join(BB.harness_cmd(A)) == G2_CMD
    A.harness_cmd = "cd ../gaia2 && python bos_gaia2.py"
    try: BB.harness_cmd(A); raise AssertionError("a cd in --harness-cmd must be rejected")
    except SystemExit: pass
    aout = os.path.join(d, "active")
    open(os.path.join(d, "act_env.txt"), "w").write("G2_STEPS=40 PYTHONHASHSEED=0 --patch none\n")
    py("bit_active.py", "tasks", "--runs", RUNS, "--instr", instr_p, "--n-tasks", "3", "--seeds", "3,4", "--env-file", os.path.join(d, "act_env.txt"),
       "--tag", "G2T_act", "--out", aout, "--harness-cmd", G2_CMD)
    al = [l for l in open(os.path.join(aout, "jobs.txt"), encoding="utf-8").read().split("\n") if l.strip()]
    assert len(al) == 2 and all(f"{G2_CMD} eval --patch none --seed" in l for l in al), al
    print("harness-cmd ok")

    # ---- AppWorld path unchanged
    if "--skip-appworld" not in sys.argv:
        r = subprocess.run([sys.executable, os.path.join(BOOST, "test_bit_offline.py")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        print(f"$ test_bit_offline.py -> {tail}")
        assert r.returncode == 0 and "BIT OFFLINE TEST OK" in r.stdout, f"AppWorld test failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}"
    print(f"G2 OFFLINE TEST OK  {d}")


if __name__ == "__main__":
    main()
