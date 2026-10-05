"""Local test of the Gaia2 harness (docs/design/GAIA2_ADAPTER_PLAN.md, U4) without ARE / vLLM: FakeG2Env (U1 API; 2 toy apps with a
read and a write tool each, AgentUserInterface, SystemApp, deterministic clock, scripted user turns, validate() comparing write counts
with a fixed oracle) and a scripted fake LLM client, injected through G2_ENV_FACTORY / G2_CLIENT_FACTORY (spawned workers import this
module, so its top level stays stdlib-only and every run is guarded by __main__).
Checks: result keys; bit_common.load_episodes reads the file; BOS_REPLAY items str / dict / ""; --replay-only (no LLM calls); hook
order vs bit_rubric.simulate (null_note at step 3, block_once, and a full trace patch); selftest (+ --twice, + a tampered file); CLI.
usage: G2_NO_REEXEC=1 py gaia2/test_g2_harness_fake.py"""
import collections, hashlib, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone
from types import SimpleNamespace as NS

HERE = os.path.dirname(os.path.abspath(__file__)); BOOST = os.path.join(os.path.dirname(HERE), "appworld", "boost")
SEND = "AgentUserInterface__send_message_to_user"
START = 1_700_000_000.0
SCEN = {
    "toy_a": {"turns": ["Buy 2 apples, add a note 'bought apples', then tell me the total price."],
              "oracle": {"Shop__buy": 1, "Notes__add_note": 1, SEND: 1}, "notifs": []},
    "toy_b": {"turns": ["Add a note 'milk'.", "Also buy one pear."],
              "oracle": {"Notes__add_note": 1, "Shop__buy": 1, SEND: 2}, "notifs": [(5.0, "Shop: pears are on sale today")]},
    "toy_c": {"turns": ["Find out how many notes I have."], "oracle": {SEND: 1}, "notifs": [(4.5, "Notes: sync completed")]},
}
TASKS = list(SCEN)
INSTR = {t: s["turns"][0] for t, s in SCEN.items()}
MAX_STEPS = 8


def _fmt(t): return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- fake environment (U1 API)
class Arg:
    def __init__(self, name, arg_type, has_default=False, default=None, description=""):
        self.name, self.arg_type, self.has_default, self.default, self.description = name, arg_type, has_default, default, description


class Tool:
    def __init__(self, app, fn, func, args, write, desc, ret="str"):
        self._public_name = f"{app}__{fn}"; self.name = fn; self.app_name = app; self.function_description = desc
        self.args = args; self.return_type = ret; self.write_operation = write; self.func = func

    def __call__(self, *a, **k): return self.func(*a, **k)


class FakeG2Env:
    def __init__(self, tid, seed, gen_seconds):
        sc = SCEN[tid]; self.tid, self.sc, self.seed = tid, sc, seed
        self.nb_turns = len(sc["turns"]); self.duration = 1800.0; self.start_time = START; self.additional_system_prompt = "Toy scenario (local test)."
        self.config = "toy"; self._t = START; self.notes = ["groceries"]; self.bought = []; self.events = []; self._turns = 0
        self._pending = [(START, "user", sc["turns"][0])] + [(START + dt, "notif", m) for dt, m in sc["notifs"]]
        self._queue = {"user": [], "notifications": []}; self.tick()

    # tools
    def _log(self, name, args, ok): self.events.append((name, args, round(self._t - START, 3), ok))

    def tools(self):
        prices = {"apple": 0.5, "pear": 0.8}

        def get_price(item):
            self._log("Shop__get_price", {"item": item}, True)
            if item not in prices: raise ValueError(f"unknown item {item}")
            return prices[item]

        def buy(item, qty=1):
            if item not in prices: self._log("Shop__buy", {"item": item, "qty": qty}, False); raise ValueError(f"unknown item {item}")
            self.bought.append((item, qty)); self._log("Shop__buy", {"item": item, "qty": qty}, True)
            return f"order-{len(self.bought)}: {qty} x {item} = {prices[item] * qty:.2f}"

        def list_notes(): self._log("Notes__list_notes", {}, True); return list(self.notes)

        def add_note(text): self.notes.append(text); self._log("Notes__add_note", {"text": text}, True); return f"note-{len(self.notes)}"

        def send(content):
            self._log(SEND, {"content": content}, True); self._turns += 1
            if self._turns < self.nb_turns: self._pending.append((self._t + 3.0, "user", self.sc["turns"][self._turns]))
            return None

        def wait(timeout):
            due = [p[0] for p in self._pending if p[0] > self._t]
            self._t = min(due + [self._t + float(timeout)]); self.tick(); return f"waited until {_fmt(self._t)}"

        def get_time(): return _fmt(self._t)
        return [Tool("Shop", "get_price", get_price, [Arg("item", "str", description="item name")], False, "Price of one item."),
                Tool("Shop", "buy", buy, [Arg("item", "str"), Arg("qty", "int", True, 1)], True, "Buy an item."),
                Tool("Notes", "list_notes", list_notes, [], False, "List all notes.", "list"),
                Tool("Notes", "add_note", add_note, [Arg("text", "str")], True, "Add a note."),
                Tool("AgentUserInterface", "send_message_to_user", send, [Arg("content", "str")], True, "Send a message to the user."),
                Tool("SystemApp", "wait_for_notification", wait, [Arg("timeout", "int")], False, "Wait for the next notification."),
                Tool("SystemApp", "get_current_time", get_time, [], False, "Current time.")]

    # clock + messages
    def now(self): return self._t
    def advance(self, seconds): self._t += float(seconds)

    def tick(self):
        due = sorted([p for p in self._pending if p[0] <= self._t], key=lambda p: p[0]); self._pending = [p for p in self._pending if p[0] > self._t]
        for t, kind, msg in due:
            if kind == "user": self._queue["user"].append(msg)
            else: self._queue["notifications"].append(f"[{_fmt(t)}] {msg}")

    def pull_messages(self):
        q = self._queue; self._queue = {"user": [], "notifications": []}; return {**q, "stop": False}

    def idle_until_message(self, cap_seconds):
        due = [p[0] for p in self._pending if p[1] == "user" and p[0] > self._t]
        if due and min(due) - self._t <= cap_seconds: self._t = min(due); self.tick()

    def first_task(self): return self.sc["turns"][0]
    def turns_done(self): return self._turns
    def stopped(self): return False
    def time_up(self): return self._t - START >= self.duration

    def validate(self):
        a = collections.Counter(n for n, _, _, ok in self.events if ok and n in ("Shop__buy", "Notes__add_note", SEND)); o = self.sc["oracle"]
        ok = all(a.get(k, 0) == v for k, v in o.items() if k != SEND) and set(k for k in a if k != SEND) <= set(o) and a.get(SEND, 0) in (o.get(SEND, 0), o.get(SEND, 0) + 1)
        keys = set(a) | set(o); G = sum(min(a.get(k, 0), o.get(k, 0)) for k in keys) / max(sum(a.values()), sum(o.values()), 1)
        return {"success": ok, "rationale": "" if ok else f"Agent and oracle counters do not match: agent {dict(sorted(a.items()))} oracle {dict(sorted(o.items()))}",
                "rationale_diag": None, "G": G, "agent_counts": dict(a), "oracle_counts": dict(o), "n_oracle_writes": sum(o.values()), "exception": None}

    def state_hash(self):
        return hashlib.sha256(json.dumps({"notes": self.notes, "bought": self.bought, "events": self.events, "now": round(self._t - START, 3), "turns": self._turns},
                                         sort_keys=True).encode()).hexdigest()


def make_fake_env(tid, seed, gen_seconds): return FakeG2Env(tid, seed, gen_seconds)


# ---------------------------------------------------------------- scripted fake LLM
NOTE_CODE = "Notes__add_note(text='bought apples')"
SCRIPTS = {   # step index -> reply | (first reply, reply to a free re-ask)
    "toy_a": ["<think>Check the price first.</think>\n```python\nprint(Shop__get_price(item='apple'))\n```",
              ("Buying now.\n```python\nr = Shop__buy(item='apple', qty=...)\n```", "```python\nr = Shop__buy(item='apple', qty=2)\nprint(r)\n```"),
              "```python\nprint(Notes__list_notes())\n```",
              f"```python\n{NOTE_CODE}\n```",
              f"```python\n{SEND}(content='Bought 2 apples for 1.00 in total.')\n```"],
    "toy_b": ["```python\nprint(SystemApp__wait_for_notification(timeout=10))\n```",
              "```python\nNotes__add_note(text='milk')\n```",
              ("I am not sure yet.", "Still thinking about it."),
              f"```python\n{SEND}(content='Added the note.')\n```",
              "```python\nprint(Shop__get_price(item='pear'))\n```",
              "```python\nShop__buy(item='pear')\n```",
              f"```python\n{SEND}(content='Bought one pear.')\n```"],
    "toy_c": ["```python\nShop__get_price()\n```",
              "```python\nfor i in range(400):\n    print('Notes__list_notes(offset=%d)' % i)\n```",
              "```python\nhelp('Shop__buy')\n```",
              "```python\nprint(len(Notes__list_notes()))\n```",
              ("<think>this reply never closes its think block", "```python\nn = len(Notes__list_notes())\nprint(n)\n```"),
              "```python\nprint(len(Notes__list_notes()))\n```"],
}
_FAILED = set()


def script_reply(tid, k, reask):
    S = SCRIPTS[tid]; e = S[min(k, len(S) - 1)]
    return (e[1] if reask else e[0]) if isinstance(e, tuple) else e


class _Completions:
    def create(self, model, messages, temperature=None, max_tokens=None, n=1, extra_body=None, **kw):
        tid = next(t for t, s in SCEN.items() if s["turns"][0] in messages[1]["content"])
        if os.environ.get("FAKE_FAIL_ONCE") == tid and tid not in _FAILED: _FAILED.add(tid); raise ConnectionError("Connection error.")
        reask = messages[-1]["role"] == "user" and messages[-1]["content"].startswith("Nothing was executed:")
        k = sum(1 for m in messages if m["role"] == "assistant") - int(reask)
        text = script_reply(tid, k, reask)
        return NS(choices=[NS(message=NS(content=text, reasoning_content=None))], usage=NS(prompt_tokens=sum(len(m["content"]) for m in messages) // 4, completion_tokens=len(text) // 4))


def make_fake_client(): return NS(chat=NS(completions=_Completions()))


# ---------------------------------------------------------------- test
NULL3 = {"name": "null_note_step3", "kind": "note", "cls": "control_flow", "hypothesis": "Null reference: a condition-free reminder at step 3.",
         "note": "Take a moment to re-read the task and check that every requirement is covered before you finish.",
         "detect_src": "def detect(view):\n    return view[\"step\"] >= 3\n", "origin": {"case_id": None, "run": "ref"}}
BLOCK_NOTE = {"name": "block_add_note", "kind": "block_once", "cls": "control_flow", "hypothesis": "Test: block the first Notes__add_note cell once.",
              "note": "Before adding a note, list the existing notes to avoid duplicates.",
              "detect_src": "def detect(view):\n    return \"Notes__add_note\" in (view[\"pending\"] or \"\")\n", "origin": {"case_id": None, "run": "ref"}}
TRACE_PATCH = '''"""trace patch: records every hook call in state["_cc_fired"] (post_exec calls are counted into the next note)."""
EDITS = [{"id": "e1", "capability": "Verification", "impl": "ControlFlow", "trigger": "always (trace)", "depends": []}]


def e1_pre_call(prompt, state):
    state.setdefault("_cc_fired", []).append({"eid": "e1", "step": state.get("_step"), "kind": "trace", "note": "pre_call pe=%d" % state.get("_pe", 0)})
    return prompt


def e1_post_parse(code, state):
    state.setdefault("_cc_fired", []).append({"eid": "e1", "step": state.get("_step"), "kind": "trace", "note": "post_parse pe=%d" % state.get("_pe", 0)})
    return code


def e1_pre_complete(code, state):
    state.setdefault("_cc_fired", []).append({"eid": "e1", "step": state.get("_step"), "kind": "trace", "note": "pre_complete pe=%d" % state.get("_pe", 0)})
    return code


def e1_post_exec(code, out, state):
    state["_pe"] = state.get("_pe", 0) + 1
'''
FAILS = []


def check(cond, label, detail=""):
    print(("ok   " if cond else "FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""), flush=True)
    if not cond: FAILS.append(label)


def main():
    os.environ.setdefault("G2_NO_REEXEC", "1")
    tmp = os.environ.get("G2_TEST_TMP") or tempfile.mkdtemp(prefix="g2_fake_")
    os.environ.update({"G2_OUT": tmp, "G2_STEPS": str(MAX_STEPS), "G2_GEN_SECONDS": "1.0", "G2_ENV_FACTORY": "test_g2_harness_fake:make_fake_env",
                       "G2_CLIENT_FACTORY": "test_g2_harness_fake:make_fake_client", "BOS_MODEL": "fake-model"})
    for k in ("BOS_REPLAY", "BOS_HINTS", "BOS_EDITS_OFF", "BOS_TASKS"): os.environ.pop(k, None)
    for p in (HERE, BOOST):
        if p not in sys.path: sys.path.insert(0, p)
    import bos_gaia2 as G, g2_hooks, bit_common, bit_rubric
    W = 2

    # 1. baseline live run (spawn pool, max_tasks_per_child=1), one transient API error on toy_c
    os.environ["FAKE_FAIL_ONCE"] = "toy_c"
    R0 = G.run_eval("none", 1, "FAKE_F0", workers=W, tasks=TASKS); os.environ.pop("FAKE_FAIL_ONCE")
    p0 = R0["_path"]; d0 = json.load(open(p0, encoding="utf-8"))
    run_keys = ["tag", "patch", "seed", "model", "history_length", "temperature", "harness_v2", "harness_h1", "harness_h11", "no_eval", "max_steps",
                "max_tokens", "backbone_extra", "n_games", "success_rate", "mean_G", "won", "G", "harm_fail", "games", "steps", "crashed", "traj", "calls",
                "api_errors", "tokens_in", "tokens_out", "finished", "bench", "gen_seconds", "think", "judge_model", "judge_hits", "judge_misses"]
    ep_keys = ["configs", "instr", "rationale", "rationale_diag", "end_reason", "nb_turns", "turns_done", "state_hash", "agent_counts", "oracle_counts", "fired"]
    step_keys = ["step", "code", "out", "resp", "exec_error", "replayed", "no_exec", "code_final", "free_retries", "t_sim", "notif", "calls", "writes", "pc", "gp", "gf"]
    check(all(k in d0 for k in run_keys + ep_keys), "result: run-level and per-episode keys", [k for k in run_keys + ep_keys if k not in d0])
    check(d0["bench"] == "gaia2" and d0["harness_h1"] is True and d0["harness_h11"] and d0["no_eval"] and d0["max_steps"] == MAX_STEPS, "result: bench / harness flags")
    check(all(len(d0[k]) == 3 for k in ep_keys + ["won", "G", "games", "traj", "crashed"]), "result: per-episode lists have one entry per task")
    check(all(all(k in s for k in step_keys) for tr in d0["traj"] for s in tr), "result: per-step keys",
          [sorted(set(step_keys) - set(s)) for tr in d0["traj"] for s in tr if not all(k in s for k in step_keys)][:3])
    check(not any(d0["crashed"]), "baseline: no crashed episode", d0["crashed"])
    ix = {t: i for i, t in enumerate(d0["games"])}; A, B, C = (d0["traj"][ix[t]] for t in TASKS)
    check(d0["won"][ix["toy_a"]] and d0["end_reason"][ix["toy_a"]] == "turns_done" and len(A) == 5, "toy_a: won, turns_done after 5 steps",
          (d0["won"][ix["toy_a"]], d0["end_reason"][ix["toy_a"]], len(A), d0["rationale"][ix["toy_a"]]))
    check(A[1]["free_retries"] == 1 and "Shop__buy(item='apple', qty=2)" in A[1]["code"], "toy_a: '...' placeholder re-asked for free", A[1])
    check([s["t_sim"] for s in A] == [1.0, 2.0, 3.0, 4.0, 5.0], "toy_a: one G2_GEN_SECONDS per step, re-asks move no clock", [s["t_sim"] for s in A])
    check(d0["won"][ix["toy_b"]] and d0["turns_done"][ix["toy_b"]] == 2 and d0["end_reason"][ix["toy_b"]] == "turns_done", "toy_b: two turns done, won",
          (d0["turns_done"][ix["toy_b"]], d0["end_reason"][ix["toy_b"]], d0["rationale"][ix["toy_b"]]))
    check("pears are on sale" in B[0]["notif"] and B[0]["t_sim"] == 5.0, "toy_b: wait_for_notification jumps to the notification", B[0])
    check(B[2]["no_exec"] == 1 and B[2]["code"] == "" and B[2]["free_retries"] == 3 and B[2]["out"].startswith("Nothing was executed this step:"), "toy_b: no_exec step after 3 free re-asks", B[2])
    check("[user message] Also buy one pear." in B[3]["out"] and B[3]["t_sim"] == 11.0, "toy_b: idle_until_message delivers turn 2 after the send", B[3])
    check(d0["end_reason"][ix["toy_c"]] == "budget" and len(C) == MAX_STEPS and not d0["won"][ix["toy_c"]], "toy_c: budget end", (d0["end_reason"][ix["toy_c"]], len(C)))
    check(C[0]["exec_error"] == 1 and C[0]["out"].startswith("Execution failed"), "toy_c: tool TypeError -> Execution failed", C[0]["out"])
    check(C[0].get("api_retries") == 1, "toy_c: transient API error retried", C[0].get("api_retries"))
    check(C[4]["free_retries"] == 1, "toy_c: unterminated <think> -> free re-ask", C[4])
    check("Agent and oracle counters do not match" in d0["rationale"][ix["toy_c"]], "toy_c: rationale from validate()", d0["rationale"][ix["toy_c"]])
    v = G.out_view("print(x)", "Notes__list_notes(offset=1)\n" * 400)
    check("[harness] output truncated:" in v and "tools not shown: Notes__list_notes" in v and len(G.out_view("help('x')", "y" * 9000)) > 8000, "out_view: H1.1 truncation marker, help cap 8000")

    # 2. bit_common.load_episodes reads the file
    eps0 = bit_common.load_episodes([p0], INSTR)
    check(len(eps0) == 3 and all(e["harness_h1"] for e in eps0) and eps0[ix["toy_b"]]["steps"][2]["no_exec"] and eps0[ix["toy_c"]]["steps"][0]["err"],
          "bit_common.load_episodes reads the result")

    # 3. BOS_REPLAY with str, dict and "" items, then live
    rep = {"toy_a": [A[0]["code"], {"exec": "print('[harness note] Your cell was NOT executed. test')", "shown": A[1]["code"]}],
           "toy_b": [B[0]["code"], B[1]["code"], ""]}
    rp = os.path.join(tmp, "replay.json"); json.dump(rep, open(rp, "w", encoding="utf-8")); os.environ["BOS_REPLAY"] = rp
    R1 = G.run_eval("none", 1, "FAKE_REP", workers=W, tasks=TASKS); os.environ.pop("BOS_REPLAY")
    d1 = json.load(open(R1["_path"], encoding="utf-8")); A1, B1, C1 = (d1["traj"][ix[t]] for t in TASKS)
    check([s["replayed"] for s in A1[:3]] == [1, 1, 0] and A1[1]["code"].startswith("print('[harness note]") and A1[1]["shown"] == A[1]["code"], "replay: str + dict items (exec / shown)", A1[:2])
    check([s["replayed"] for s in B1[:4]] == [1, 1, 1, 0] and B1[2]["no_exec"] == 1 and B1[2]["out"].startswith("Nothing was executed this step.") and B1[2]["t_sim"] == B[2]["t_sim"],
          "replay: '' item = no exec, clock still advances", B1[2])
    check([s["t_sim"] for s in B1] == [s["t_sim"] for s in B] and [s["out"] for s in B1[3:]] == [s["out"] for s in B[3:]], "replay: same clock / outputs after the replayed prefix")
    check(d1["calls"] < d0["calls"], "replay: fewer LLM calls", (d1["calls"], d0["calls"]))
    eps1 = bit_common.load_episodes([R1["_path"]], INSTR)
    check(eps1[ix["toy_b"]]["has_replay"] and eps1[ix["toy_b"]]["steps"][2]["replayed"], "replay: load_episodes sees replayed steps")

    # 4. --replay-only: no LLM calls; a partial prefix ends with replay_end
    full = {d0["games"][i]: G.replay_items(d0["traj"][i]) for i in range(3)}; full["toy_c"] = full["toy_c"][:3]
    R2 = G.run_eval("none", 1, "FAKE_RO", workers=W, tasks=TASKS, replay=full, hints={}, replay_only=True)
    check(R2["calls"] == 0 and R2["api_errors"] == 0, "replay-only: zero LLM calls", R2["calls"])
    check([R2["state_hash"][i] for i in (ix["toy_a"], ix["toy_b"])] == [d0["state_hash"][i] for i in (ix["toy_a"], ix["toy_b"])] and R2["won"] == [d0["won"][0], d0["won"][1], False],
          "replay-only: full replay reproduces state_hash / won")
    check(R2["end_reason"][ix["toy_c"]] == "replay_end" and R2["steps"][ix["toy_c"]] == 3, "replay-only: partial prefix ends with replay_end", (R2["end_reason"], R2["steps"]))

    # 5. hook order fidelity vs bit_rubric.simulate
    pre_complete_ok = "send_message_to_user" in open(os.path.join(BOOST, "bit_rubric.py"), encoding="utf-8").read()
    for spec in (NULL3, BLOCK_NOTE):
        src = bit_rubric.compile_patch([spec], max_steps=MAX_STEPS); pp = os.path.join(tmp, f"{spec['name']}.py"); open(pp, "w", encoding="utf-8").write(src)
        g2_hooks.load_v3(pp)   # compile_patch output loads in g2_hooks.load_v3
        sim = bit_rubric.simulate(src, eps0, timeout_s=60)
        pred = {e["task"]: (sim[e["eid"]]["fires"][0]["k"] if sim[e["eid"]]["fires"] else None) for e in eps0}
        Rp = G.run_eval(pp, 1, f"FAKE_{spec['name']}", workers=W, tasks=TASKS)
        live = {t: (Rp["fired"][i][0]["step"] if Rp["fired"][i] else None) for i, t in enumerate(Rp["games"])}
        check(pred == live and any(v is not None for v in live.values()), f"fidelity {spec['kind']} ({spec['name']}): simulate fire k == live fire k", (pred, live))
        if spec["kind"] == "block_once":
            ib = ix["toy_a"]; kb = live["toy_a"]; sb = Rp["traj"][ib][kb]
            check(sb["code"].startswith("print('[harness note] Your cell was NOT executed.") and "[harness note] Your cell was NOT executed." in sb["out"], "block_once: blocked cell prints the note", sb)
        else:
            check(all(Rp["traj"][i][3]["pc"] == 1 for i in range(3)) and all(s["pc"] == 0 for i in range(3) for s in Rp["traj"][i] if s["step"] != 3), "null_note: pc=1 only at step 3")
    tp = os.path.join(tmp, "trace_patch.py"); open(tp, "w", encoding="utf-8").write(TRACE_PATCH)
    for label, replay in (("live", {}), ("replayed prefix", rep)):
        Rt = G.run_eval(tp, 1, "FAKE_TRACE", workers=W, tasks=TASKS, replay=replay, hints={}); epst = bit_common.load_episodes([Rt["_path"]], INSTR)
        sim = bit_rubric.simulate(TRACE_PATCH, epst, stop_at_first=False, timeout_s=60); bad = []
        for i, e in enumerate(epst):
            lv = [(f["step"], f["note"]) for f in Rt["fired"][i] if pre_complete_ok or not f["note"].startswith("pre_complete")]
            sv = [(f["k"], f["note"]) for f in sim[e["eid"]]["fires"]]
            if lv != sv: bad.append((e["task"], lv[:6], sv[:6]))
        check(not bad, f"fidelity trace patch ({label}): every pre_call / post_parse{' / pre_complete' if pre_complete_ok else ''} call and the post_exec count before it match simulate", bad[:1])
        if label == "live":
            n_pc = sum(1 for f in Rt["fired"][ix["toy_a"]] if f["note"].startswith("pre_complete"))
            check(n_pc == 1, "trace: pre_complete runs once, on the send_message_to_user cell", n_pc)
    if not pre_complete_ok: print("note: bit_rubric still uses the 'complete_task' marker (U6 pending); pre_complete calls were excluded from the trace comparison")

    # 6. selftest: replay vs original, two replays, tampered file; CLI (re-exec path, PYTHONHASHSEED unset)
    st = G.selftest(p0, n=10, twice=False, workers=W); check(st["ok"] and st["n"] == 3, "selftest: replay == original", st["episodes"])
    st2 = G.selftest(R1["_path"], n=10, twice=True, workers=W); check(st2["ok"], "selftest --twice (file with replayed / dict / '' steps)", st2["episodes"])
    st3 = G.selftest(Rp["_path"], n=10, twice=False, workers=W); check(st3["ok"], "selftest: block_once run replays exactly", st3["episodes"])
    bad = json.load(open(p0, encoding="utf-8")); bad["state_hash"][0] = "0" * 64; bad["traj"][1][0]["out"] = "tampered"; bad["tag"] = "FAKE_BAD"
    pb = os.path.join(tmp, "bad.json"); json.dump(bad, open(pb, "w", encoding="utf-8"))
    st4 = G.selftest(pb, n=10, workers=W); check(not st4["ok"] and st4["n_mismatch"] == 2, "selftest: detects tampered state_hash / out", st4["n_mismatch"])
    env = {k: v for k, v in os.environ.items() if k not in ("G2_NO_REEXEC", "PYTHONHASHSEED")}
    r = subprocess.run([sys.executable, os.path.join(HERE, "bos_gaia2.py"), "selftest", "--result", p0, "--workers", "2"], env=env, capture_output=True, text=True, timeout=600)
    check(r.returncode == 0 and os.path.exists(os.path.join(tmp, "results", "selftest_FAKE_F0.json")), "CLI selftest (re-exec with PYTHONHASHSEED=0) exits 0", r.stdout[-500:] + r.stderr[-1500:])
    r = subprocess.run([sys.executable, os.path.join(HERE, "bos_gaia2.py"), "selftest", "--result", pb, "--workers", "2"], env=env, capture_output=True, text=True, timeout=600)
    check(r.returncode == 1, "CLI selftest exits 1 on mismatch", r.returncode)
    tj = os.path.join(tmp, "tasks.json"); json.dump(TASKS, open(tj, "w")); rj = os.path.join(tmp, "replay_full.json"); json.dump(full, open(rj, "w"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "bos_gaia2.py"), "eval", "--patch", "none", "--seed", "1", "--tag", "FAKE_CLI", "--workers", "2", "--replay-only"],
                       env={**env, "BOS_TASKS": tj, "BOS_REPLAY": rj}, capture_output=True, text=True, timeout=600)
    dc = json.load(open(os.path.join(tmp, "results", "FAKE_CLI_seed1.json"), encoding="utf-8")) if r.returncode == 0 else {}
    check(r.returncode == 0 and dc.get("calls") == 0 and dc.get("state_hash", [None])[ix["toy_a"]] == d0["state_hash"][ix["toy_a"]], "CLI eval --replay-only", r.stderr[-1500:])

    print(f"\n{'ALL PASSED' if not FAILS else f'{len(FAILS)} FAILED: {FAILS}'}  (outputs in {tmp})")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
