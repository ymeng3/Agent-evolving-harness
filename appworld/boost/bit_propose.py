"""BIT Unit D (docs/design/BIT_IMPLEMENTATION_PLAN.md): hindsight self-proposer. One call per memory-tree case (bit_tree.py tree.json,
top --n-cases) to the SAME backbone (proposer.chat, thinking on). The prompt carries privileged hindsight -- the task, the outcome (+ G),
the failed run and its won sibling step by step with reasoning tails -- but the candidates are constrained specs (NOTE + a pure
def detect(view) over the executed prefix, kind note | block_once) that bit_rubric compiles into a v3 patch. Each candidate is validated,
compiled and self-checked by offline replay (must fire on the case's lost episode, must not fire on its won sibling); failures are fed back
verbatim, <= 2 retries per candidate. One JSONL line per candidate; compiled patches go to appworld/patches_ccbit/<cid>.py.
usage: python boost/bit_propose.py --tree bit/<R>/tree.json --runs A.json,B.json --instr instructions_all100.json --out cands_<run>.jsonl
           --run-id P1 [--n-cases 20 --k-per-case 2 --no-sibling --outcome-detail {won,G} --failed-tests ft.json --workers 6
           --max-tokens 16000 --patch-dir patches_ccbit --dry-run]
env: BOS_BASE_URL, BOS_API_KEY, BOS_MODEL (proposer.chat), BOOST_EFFORT (optional), BOOST_TIMEOUT; BOOST_MOCK=1 = offline mock replies."""
import argparse, json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); AW = os.path.dirname(HERE)
if HERE not in sys.path: sys.path.insert(0, HERE)
import proposer as PR, bit_rubric as R
from bit_common import load_episodes
from bit_tree import common_prefix

MAX_RETRIES = 2; CODE_CHARS = 800; OUT_CHARS = 200; TAIL_CHARS = 400

SYSTEM = ("You review logs of an LLM agent (a model like yourself) solving AppWorld tasks. You find the step and the mechanism that made a run "
          "fail, and you write small, general detector programs that let the harness warn the agent at the right moment in future runs.")

VIEW_SCHEMA = '''view = {"task": str,            # instruction (state["_instr"])
        "step": int,            # harness step index about to run (counts no_exec steps)
        "max_steps": 30,
        "cells": [{"code": str, "out": str, "error": bool}, ...],  # executed cells so far, in order (no_exec skipped); out <= 200 chars
        "pending": str | None}  # block_once: code about to execute; note: None
# detect(view) -> falsy (no fire) | True (fire with NOTE) | non-empty str (fire with this note, <= 600 chars)'''

# format only; deliberately an unrelated mechanism (never put an answer/complete_task rule here: it is the rediscovery benchmark)
EXAMPLE = '''NAME: same_failing_call_three_times
KIND: note
CLASS: control_flow
HYPOTHESIS: When the last three executed cells made the same API call and all three failed, the agent is looping on a wrong call; pointing it to the API's documentation breaks the loop.
```python
NOTE = "Your last three cells made the same API call and each one failed. Repeating it will fail again: read this API's documentation with apis.api_docs.show_api_doc(app_name=..., api_name=...) and fix the arguments before calling it again."
def detect(view):
    import re
    last = view["cells"][-3:]
    if len(last) < 3 or not all(c["error"] for c in last):
        return False
    calls = [tuple(re.findall(r"apis\\.\\w+\\.\\w+", c["code"])) for c in last]
    return bool(calls[0]) and calls[0] == calls[1] == calls[2]
```'''


# ---------------------------------------------------------------- prompt
def _clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[:n] + f" ...[+{len(s) - n} chars]"


def _indent(s, pre="      "):
    return "\n".join(pre + l for l in (s or "").splitlines()) or pre


def reasoning_tail(resp, n=TAIL_CHARS):
    """the logged response tail (resp is stored as resp[-600:]) without its code block(s): the last n chars of the reasoning."""
    t = re.sub(r"```(?:python|py)?[ \t]*\n.*?(```|$)", " ", resp or "", flags=re.S).strip()
    t = re.sub(r"\s*\n\s*\n\s*", "\n", t)
    return ("..." + t[-n:]) if len(t) > n else t


def fmt_step(s):
    k = s["k"]; head = f"[step {k}]" + (" (replayed)" if s.get("replayed") else "")
    lines = [head]
    tail = reasoning_tail(s.get("resp"))
    if tail: lines.append("  [reasoning tail, NOT visible to the detector]\n" + _indent(tail))
    if s["no_exec"]:
        lines.append("  (nothing was executed at this step: no valid code block; this step is NOT in view['cells'])")
    else:
        lines.append("  code:\n" + _indent(_clip(s["code"], CODE_CHARS)))
        lines.append("  -> out" + (" (ERROR)" if s["err"] else "") + ":\n" + _indent(s["out"][:OUT_CHARS]))
    return "\n".join(lines)


def _outcome(ep, detail, max_steps):
    n = len(ep["steps"]); done = any("complete_task" in (s["code"] or "") for s in ep["steps"] if not s["no_exec"])
    o = "SUCCEEDED" if ep["won"] else "FAILED"
    if detail == "G" and ep.get("G") is not None: o += f", G = {ep['G']:.2f}"
    return f"{o}; {n} of {max_steps} steps used; " + ("it called complete_task." if done else "it never called complete_task (the budget ran out).")


def build_prompt(case, eps_by, max_steps=30, k=2, outcome_detail="G", no_sibling=False, failed_tests=None):
    lost = eps_by[case["lost"]]; won = None if no_sibling or not case.get("won") else eps_by[case["won"]]
    fd = common_prefix(lost, won) if won else 0
    P = []
    P.append("## 1. The harness\n"
             "An LLM agent solves AppWorld tasks: everyday tasks over simulated apps (amazon, gmail, venmo, spotify, phone, file_system, ...) that "
             "it reaches from python through `apis.<app>.<api>(...)`. At each step the agent writes ONE python code cell; the harness executes it "
             f"and shows the output. The budget is {max_steps} steps (step indices 0..{max_steps - 1}). The episode ends when the agent calls "
             "`apis.supervisor.complete_task(...)` or when the budget runs out; the environment's tests then check the final state of the apps.\n"
             "You can add a HARNESS RULE: a detector `detect(view)` plus a short NOTE. The harness evaluates the detector during future episodes "
             "(of any task) and, when it fires, shows the note to the agent.")
    P.append("## 2. What the detector sees (hard rule)\n`detect` receives only this `view` (exact schema):\n```python\n" + VIEW_SCHEMA.replace('"max_steps": 30', f'"max_steps": {max_steps}') + "\n```\n"
             "HARD RULE: detect sees nothing but `view`; it must be decidable from the prefix observed so far. It cannot see the agent's reasoning, "
             "outputs beyond their first 200 characters, the task id, the outcome, the evaluation tests, or anything that happens later in the "
             "episode. It must be a pure function of view: no I/O; imports only inside detect and only from re, json, math, random, collections, "
             "itertools, string; open/exec/eval/getattr/setattr/globals and dunder names are forbidden.")
    P.append("## 3. Kinds\n"
             "- `note`: detect is called before each step's LLM call (`view[\"pending\"]` is None). The first time it fires, \"[harness note] "
             "<note>\" is appended to that step's prompt. It fires at most once per episode.\n"
             "- `block_once`: detect is called after the agent wrote its cell and before the cell is executed (`view[\"pending\"]` = that code). "
             "The first time it fires, the cell is NOT executed: the agent gets \"[harness note] Your cell was NOT executed. <note>\" as the output "
             "and writes the step again, and that second attempt is executed whatever it is (at most one block per episode). block_once never "
             f"fires at step >= {max_steps - 1} (the last step, max_steps-1), because the agent could not act on the note afterwards.\n"
             "Use block_once when the harmful action is visible in the cell about to run and must be stopped before it executes; use note when "
             "the signal is in what has already happened.\n"
             "CLASS: `control_flow` (how the agent works: order of steps, checks, retries, budget use) or `task_knowledge` (facts about the apps, "
             "APIs or task conventions that the agent got wrong).")
    C = [f"## 4. The case\nTask instruction: {lost['instr']}"]
    if outcome_detail == "G":
        C.append("G = the fraction of the task's evaluation tests that pass on the final state; the task counts as solved only if every test "
                 "passes (G = 1.00). A G close to 1 means only a few checks failed.")
    C.append(f"FAILED run: {_outcome(lost, outcome_detail, max_steps)}")
    if won: C.append(f"SUCCESSFUL run of the same task: {_outcome(won, outcome_detail, max_steps)}")
    elif not no_sibling: C.append("(No successful run of this task is available.)")
    ft = (failed_tests or {}).get(case["lost"])
    if ft: C.append("Evaluation tests that FAILED in the failed run:\n" + "\n".join(f"- {t}" for t in ft))
    C.append("Notation: [step k] = harness step index k (= view['step'] when that step is about to run); code is cut at "
             f"{CODE_CHARS} chars, outputs at {OUT_CHARS} chars (the detector sees the same 200 chars).")
    if won and fd > 0:
        C.append(f"### Steps 0..{lost['steps'][fd - 1]['k']}: IDENTICAL in both runs (same code, same output), shown once\n" + "\n".join(fmt_step(s) for s in lost["steps"][:fd]))
        C.append(f"### FAILED run, from the fork on\n" + ("\n".join(fmt_step(s) for s in lost["steps"][fd:]) or "(no further steps)"))
        C.append(f"### SUCCESSFUL run, from the fork on\n" + ("\n".join(fmt_step(s) for s in won["steps"][fd:]) or "(no further steps)"))
    else:
        C.append("### FAILED run, all steps\n" + "\n".join(fmt_step(s) for s in lost["steps"]))
        if won: C.append("### SUCCESSFUL run, all steps\n" + "\n".join(fmt_step(s) for s in won["steps"]))
    P.append("\n\n".join(C))
    sib = " and must NOT fire anywhere on the successful run" if won else ""
    P.append("## 5. What to write\n"
             "First, in at most 3 sentences: the decisive step of the failed run (the step after which the failure was fixed in place and never "
             "corrected) and the mechanism (what went wrong and why).\n"
             f"Then write {k} different candidate rules. Each candidate must:\n"
             f"- fire on the failed run at or before its decisive step{sib};\n"
             "- be GENERAL: fire whenever the same mechanism is about to happen on other tasks too. No task-specific names, ids, product or "
             "person names, numbers or long literal strings from this case; key on the structure of the code, the outputs and the task wording;\n"
             "- have a NOTE (20..600 chars) that is factual and actionable: what the harness observed and what the agent should check or do. "
             "It must NOT contain the solution of this task (no ids, names or values from this case).\n"
             f"Each candidate is checked automatically by replaying the run(s) above through it: it must fire on the failed run{sib}. "
             "If a check fails you get the exact reason back and can fix the candidate.")
    P.append("## 6. Output format\n<the decisive step and mechanism, at most 3 sentences>\n\nthen, for each candidate:\n"
             "NAME: <snake_case, <= 40 chars>\nKIND: note | block_once\nCLASS: control_flow | task_knowledge\n"
             "HYPOTHESIS: <one or two sentences: the mechanism, and why the note helps>\n```python\nNOTE = \"...\"\ndef detect(view):\n    ...\n```\n"
             "Only `NOTE = \"...\"` and `def detect(view):` may appear at the top level of the block; put imports and helpers inside detect. "
             "detect returns False/None (no fire), True (fire with NOTE) or a non-empty string (fire with that string as the note).\n\n"
             "Format example (an unrelated mechanism, shown for the format only):\n" + EXAMPLE)
    return "\n\n".join(P)


# ---------------------------------------------------------------- calls
def _chat_effort(messages, max_tokens, effort):
    """proposer.chat with an explicit reasoning effort (BOOST_EFFORT is read from the process env, which threads must not mutate)."""
    from openai import OpenAI
    cl = OpenAI(api_key=os.environ["BOS_API_KEY"], base_url=os.environ["BOS_BASE_URL"], timeout=float(os.environ.get("BOOST_TIMEOUT", "1800")), max_retries=0)
    last = None
    for att in range(4):
        try:
            r = cl.chat.completions.create(model=os.environ.get("BOS_MODEL", "qwen/qwen3.8-27b"), messages=messages, temperature=0.7, max_tokens=max_tokens,
                                           extra_body={"chat_template_kwargs": {"enable_thinking": True, "reasoning_effort": effort}})
            return r.choices[0].message.content or "", {"in": r.usage.prompt_tokens, "out": r.usage.completion_tokens, "finish": r.choices[0].finish_reason}
        except Exception as e:
            last = e; time.sleep(5 * (att + 1))
    return "", {"in": 0, "out": 0, "finish": f"error: {str(last)[:120]}"}


def ask(messages, max_tokens, mock_key=0):
    """one proposer turn; an empty reply cut by the length limit is retried once at effort medium. -> (text, [usage, ...])"""
    mock = os.environ.get("BOOST_MOCK") == "1"
    text, u = _mock_chat(messages, None, mock_key) if mock else PR.safe_chat(messages, max_tokens=max_tokens)
    uses = [u]
    if not (text or "").strip() and u.get("finish") == "length":
        text, u2 = _mock_chat(messages, "medium", mock_key) if mock else _chat_effort(messages, max_tokens, "medium")
        uses.append({**u2, "effort": "medium"})
    return _strip_think(text), uses


def _strip_think(text):
    text = text or ""
    return text.split("</think>", 1)[1] if "</think>" in text else text


# ---------------------------------------------------------------- check
def _first_detect_error(spec, ep, max_steps):
    """in-process: the first exception detect raises on ep's views (only called after a simulation of the same views terminated)."""
    ns = {}
    try: exec(compile(spec["detect_src"], "<detect>", "exec"), ns)
    except Exception as e: return f"{type(e).__name__}: {e}"
    cells = []
    for s in ep["steps"]:
        if not s.get("replayed"):
            blk = spec["kind"] == "block_once"
            if not (blk and (s["no_exec"] or s["k"] >= max_steps - 1)):
                view = {"task": ep["instr"], "step": s["k"], "max_steps": max_steps, "cells": [dict(c) for c in cells], "pending": s["code"] if blk else None}
                try: ns["detect"](view)
                except Exception as e: return f"{type(e).__name__}: {str(e)[:200]} (at step {s['k']})"
        if not s["no_exec"]: cells.append({"code": s["code"], "out": s["out"][:200], "error": s["err"]})
    return ""


def no_check():
    """self_check of a candidate that never reached the replay (keys always present; None = not measured)."""
    return {"fires_lost": None, "k_lost": None, "fires_won": None, "k_won": None, "n_steps_lost": None, "hook_errors": None}


def check(spec, lost, won, max_steps, sim_timeout, enforce_won=True):
    """-> (patch_src | None, self_check dict, why). why == "" iff the candidate passes."""
    try:
        R.validate_spec(spec); src = R.compile_patch([spec], max_steps)
    except Exception as e:
        return None, no_check(), f"rejected by the validator: {e}"
    eps = [lost] + ([won] if won else [])
    try: res = R.simulate(src, eps, timeout_s=sim_timeout)
    except R.SimulationError as e: return src, no_check(), f"the offline replay failed: {e}"
    fl, fw = res[lost["eid"]]["fires"], (res[won["eid"]]["fires"] if won else [])
    sc = {"fires_lost": bool(fl), "k_lost": fl[0]["k"] if fl else None, "fires_won": bool(fw) if won else None, "k_won": fw[0]["k"] if fw else None,
          "n_steps_lost": len(lost["steps"]), "hook_errors": sum(r["hook_errors"] for r in res.values())}
    if not fl:
        why = "detect never fired on the FAILED run; it must fire there, at or before the decisive step."
        n_err = res[lost["eid"]]["hook_errors"]
        if n_err:
            err = _first_detect_error(spec, lost, max_steps)
            why += f" On the failed run detect raised an exception {n_err} time(s) (an exception counts as no fire)" + (f"; the first one: {err}" if err else "") + "."
        elif spec["kind"] == "block_once":
            why += f" (block_once is evaluated on each executed cell's code as view['pending'], never at step >= {max_steps - 1}.)"
        return src, sc, why
    if fw and enforce_won:
        s = next((x for x in won["steps"] if x["k"] == fw[0]["k"]), None)
        cell = f"; the pending cell was:\n{_clip(s['code'], 300)}" if s and spec["kind"] == "block_once" else ""
        return src, sc, (f"detect fired on the SUCCESSFUL run at step {fw[0]['k']}{cell}\nIt must not fire on the successful run: make the condition "
                         "specific to what goes wrong in the failed run.")
    return src, sc, ""


FIX = ("Candidate {name}: {why}\nRewrite this one candidate to fix the problem. Reply with exactly one candidate in the same format (NAME:, KIND:, "
       "CLASS:, HYPOTHESIS:, then one ```python block with NOTE = \"...\" and def detect(view):).")
NONE_FOUND = ("Your reply contained no candidate in the required format. Write the {k} candidates now: for each, NAME:, KIND:, CLASS:, HYPOTHESIS: "
              "lines, then one ```python block with NOTE = \"...\" and def detect(view):.")


def _usage_sum(uses):
    return {"in": sum(u.get("in") or 0 for u in uses), "out": sum(u.get("out") or 0 for u in uses), "calls": uses}


def run_case(ci, case, eps_by, a, failed_tests, write):
    lost = eps_by[case["lost"]]; won = eps_by[case["won"]] if case.get("won") else None
    prompt_won = None if a.no_sibling else won
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": build_prompt(case, eps_by, a.max_steps, a.k_per_case, a.outcome_detail, a.no_sibling, failed_tests)}]
    t0 = time.time(); text, uses = ask(msgs, a.max_tokens, ci); specs = R.parse_proposals(text); conv = msgs + [{"role": "assistant", "content": text}]; n_whole = 0
    while not specs and n_whole < MAX_RETRIES:   # nothing parseable at all: ask again for the whole set
        n_whole += 1; conv = conv + [{"role": "user", "content": NONE_FOUND.format(k=a.k_per_case)}]
        text, u = ask(conv, a.max_tokens, ci); uses += u; specs = R.parse_proposals(text); conv = conv + [{"role": "assistant", "content": text}]
    diagnosis = (text.split("NAME:", 1)[0] if specs else text).strip()[:2000]
    base = {"run": a.run_id, "case_id": case["case_id"], "task": case["task"], "lost": case["lost"], "won": case.get("won"), "shown_won": bool(prompt_won),
            "outcome_detail": a.outcome_detail, "diagnosis": diagnosis}
    if not specs:
        write({"cid": f"{a.run_id}_{case['case_id']}_1", **base, "spec": None, "valid": False, "why": "no candidate in the reply" + (f" (finish={uses[-1].get('finish')})" if uses else ""),
               "self_check": no_check(), "patch_path": None, "attempts": n_whole + 1, "usage": _usage_sum(uses), "raw": text})
        return 0, 1
    n_ok = 0
    for j, spec in enumerate(specs[:a.k_per_case], 1):
        cid = f"{a.run_id}_{case['case_id']}_{j}"; cu = list(uses) if j == 1 else []; raw = text; hist = []; cconv = conv
        for att in range(MAX_RETRIES + 1):
            spec["origin"] = {"case_id": case["case_id"], "run": a.run_id}
            src, sc, why = check(spec, lost, won, a.max_steps, a.sim_timeout, enforce_won=not a.no_sibling)   # --no-sibling: won recorded only
            hist.append({"name": spec.get("name"), "why": why})
            if not why or att == MAX_RETRIES: break
            cconv = cconv + [{"role": "user", "content": FIX.format(name=spec.get("name") or f"#{j}", why=why)}]
            rt, u = ask(cconv, a.max_tokens, ci); cu += u; cconv = cconv + [{"role": "assistant", "content": rt}]
            new = R.parse_proposals(rt); raw = rt
            spec = new[0] if new else {**spec, "detect_src": "", "note": ""}   # unparseable fix -> the validator names what is missing
        path = None
        if src:
            os.makedirs(a.patch_dir, exist_ok=True); fp = os.path.join(a.patch_dir, f"{cid}.py")
            with open(fp, "w", encoding="utf-8") as f: f.write(src)
            ap_ = os.path.abspath(fp); path = os.path.relpath(ap_, AW).replace("\\", "/") if ap_.startswith(os.path.abspath(AW) + os.sep) else ap_
        write({"cid": cid, **base, "spec": spec, "valid": not why, "why": why, "self_check": sc, "patch_path": path, "attempts": len(hist), "history": hist,
               "usage": _usage_sum(cu), "raw": raw, "secs": round(time.time() - t0, 1)})
        n_ok += not why
    return n_ok, min(len(specs), a.k_per_case)


# ---------------------------------------------------------------- mock (BOOST_MOCK=1; offline tests only)
_D10_LIKE = '''NAME: answer_on_action_task
KIND: block_once
CLASS: task_knowledge
HYPOTHESIS: mock-only test data (a D10-like rule): an answer passed to complete_task on a task that asks no question.
```python
NOTE = "This task does not ask a question. If it is done, call apis.supervisor.complete_task() without an answer."
def detect(view):
    import re
    if "?" in view["task"]:
        return False
    m = re.search(r"complete_task\\(\\s*answer\\s*=\\s*([^)]*)\\)", view["pending"] or "")
    return bool(m) and m.group(1).strip() != "None"
```
'''
_GETATTR = '''NAME: uses_getattr
KIND: note
CLASS: control_flow
HYPOTHESIS: mock: invalid on purpose (forbidden name).
```python
NOTE = "The harness noticed something odd in the last cell; check its output again before going on."
def detect(view):
    return getattr(view, "cells", None)
```
'''
_NEVER = '''NAME: never_fires
KIND: note
CLASS: control_flow
HYPOTHESIS: mock: valid but never fires.
```python
NOTE = "You have used more steps than the budget allows; finish the task now."
def detect(view):
    return view["step"] > 99
```
'''
_TWO_CELLS = '''NAME: after_two_cells
KIND: note
CLASS: control_flow
HYPOTHESIS: mock: fires as soon as two cells have been executed (fires on won siblings too).
```python
NOTE = "Two cells are done; re-read the task and list every requirement before the next write."
def detect(view):
    return len(view["cells"]) >= 2
```
'''
_MOCK_SCRIPTS = [   # case index % 4 -> turn -> reply; turn = number of assistant turns already in the conversation
    {0: "The decisive step is the last one (mock diagnosis).\n\n" + _D10_LIKE + "\n" + _GETATTR, 1: _TWO_CELLS, 2: _TWO_CELLS},
    {0: "Mock diagnosis.\n\n" + _NEVER, 1: _NEVER, 2: _NEVER},
    {0: "", 1: _TWO_CELLS, 2: _TWO_CELLS},           # empty + finish=length at default effort -> retried at medium
    {0: "I think the agent should be more careful.", 1: _D10_LIKE, 2: _D10_LIKE},   # no candidate -> whole-call retry
]


def _mock_chat(messages, effort, key):
    sc = _MOCK_SCRIPTS[key % len(_MOCK_SCRIPTS)]; turn = sum(1 for m in messages if m["role"] == "assistant")
    if key % len(_MOCK_SCRIPTS) == 2 and turn == 0:
        return (_TWO_CELLS, {"in": 0, "out": 0, "finish": "mock"}) if effort == "medium" else ("", {"in": 0, "out": 0, "finish": "length"})
    return sc.get(turn, sc[max(sc)]), {"in": 0, "out": 0, "finish": "mock"}


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True); ap.add_argument("--runs", required=True, help="comma list of the run logs the tree was built from")
    ap.add_argument("--instr", required=True); ap.add_argument("--out", required=True, help="cands_<run>.jsonl")
    ap.add_argument("--run-id", required=True); ap.add_argument("--n-cases", type=int, default=20); ap.add_argument("--k-per-case", type=int, default=2)
    ap.add_argument("--no-sibling", action="store_true", help="ablation: do not show the won sibling (its self-check is recorded, not enforced)")
    ap.add_argument("--outcome-detail", choices=["won", "G"], default="G"); ap.add_argument("--failed-tests", default="", help="json {eid: [test names]}")
    ap.add_argument("--workers", type=int, default=6); ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--max-steps", type=int, default=30); ap.add_argument("--sim-timeout", type=float, default=60)
    ap.add_argument("--patch-dir", default=os.path.join(AW, "patches_ccbit")); ap.add_argument("--cases", default="", help="comma list of case ids (overrides --n-cases)")
    ap.add_argument("--dry-run", action="store_true", help="print the first case's full prompt and exit (no calls)")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", a.run_id): sys.exit("--run-id must be [A-Za-z0-9_-]+")
    tree = json.load(open(a.tree, encoding="utf-8"))
    cases = [c for c in tree["cases"] if c["case_id"] in a.cases.split(",")] if a.cases else tree["cases"][:a.n_cases]
    eps_by = {e["eid"]: e for e in load_episodes(a.runs, a.instr) if not e["crashed"]}
    miss = [x for c in cases for x in (c["lost"], c.get("won")) if x and x not in eps_by]
    if miss: sys.exit(f"episodes of the tree missing from --runs: {miss[:5]}")
    ft = json.load(open(a.failed_tests, encoding="utf-8")) if a.failed_tests else None
    if a.dry_run:
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass
        c = cases[0]; print(f"### SYSTEM\n{SYSTEM}\n\n### USER (case {c['case_id']}: lost={c['lost']} won={c.get('won')})\n"
                            + build_prompt(c, eps_by, a.max_steps, a.k_per_case, a.outcome_detail, a.no_sibling, ft))
        return
    if os.path.dirname(a.out): os.makedirs(os.path.dirname(a.out), exist_ok=True)
    lock = threading.Lock(); fh = open(a.out, "w", encoding="utf-8")

    def write(rec):
        with lock: fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()

    def one(ic):
        i, c = ic
        try: return run_case(i, c, eps_by, a, ft, write)
        except Exception as e:   # never lose the other cases to one broken case
            write({"cid": f"{a.run_id}_{c['case_id']}_1", "run": a.run_id, "case_id": c["case_id"], "task": c["task"], "spec": None, "valid": False,
                   "why": f"proposer crashed: {type(e).__name__}: {str(e)[:300]}", "self_check": no_check(), "patch_path": None, "usage": None, "raw": ""})
            return 0, 1
    t0 = time.time()
    with ThreadPoolExecutor(max(1, a.workers)) as ex: res = list(ex.map(one, enumerate(cases)))
    fh.close()
    print(f"{a.run_id}: {len(cases)} cases, {sum(r[1] for r in res)} candidates, {sum(r[0] for r in res)} valid -> {a.out} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
