EDITS = [
    {"id": "e1", "capability": "Planning", "impl": "Prompt",
     "trigger": "rubric detectors D7 (<=3 steps left, not completed) > D2 (last two cells identical up to literals) > D6 (supervisor ids in an amazon episode) > D8' (re-read of an already-read spec); at most ONE note per step, per-detector cooldown",
     "depends": [], "expected_effect": "grounded, specific, single-action nudges (literature checklist: AutoGuide, Leins et al. 2026, SWE-agent, Anthropic tool-writing)",
     "side_effect_risk": "false-positive nudges; premature completion"},
]


def e1_post_exec(code, out, state):
    state.setdefault("cells", []).append([code or "", (out or "")[:400]])


def e1_pre_call(prompt, state):
    import re
    state["step"] = state.get("step", -1) + 1
    step = state["step"]; cells = state.get("cells", []); left = 30 - step
    last = state.setdefault("last_fired", {})
    def ok(name, cool):
        return step - last.get(name, -99) >= cool
    calls = lambda c: re.findall(r"apis\.([a-z_]+)\.([a-z_]+)\s*\(", c)
    done = any(re.search(r"apis\.supervisor\.complete_task\s*\(", c) for c, _ in cells)
    note = None
    # D7 end of budget (highest priority)
    if note is None and left <= 3 and not done and ok("D7", 2):
        last["D7"] = step
        note = (f"Only {left} step(s) remain and complete_task has not been called. If the requested changes are already made, call "
                f"apis.supervisor.complete_task() (with answer=... if the task asks a question) now; otherwise make the single remaining "
                f"state-changing call and complete_task in this same step, because unfinished tasks score zero.")
    # D2 per-item cells
    if note is None and len(cells) >= 2 and ok("D2", 3):
        lit = re.compile(r"""("([^"\\]|\\.)*"|'([^'\\]|\\.)*'|\b\d+(\.\d+)?\b)""")
        norm = lambda s: " ".join(lit.sub("#", s).split())
        a, b = cells[-2][0], cells[-1][0]; cb = [x for x in calls(b) if x[0] != "api_docs"]
        if a != b and norm(a) == norm(b) and cb:
            last["D2"] = step; app_, api_ = cb[-1]
            note = (f"Your last two steps called apis.{app_}.{api_} once per item. Do all remaining items in ONE step, e.g.\n"
                    f"results = []\nfor item in items:  # the remaining items\n    results.append(apis.{app_}.{api_}(...))\nprint(results)\n"
                    f"so the per-item calls do not use up the 30-step budget.")
    # D6 wrong data source
    if note is None and cells and ok("D6", 30):
        uses_amazon = any("apis.amazon." in c for c, _ in cells)
        if uses_amazon and re.search(r"apis\.supervisor\.(show_addresses|show_payment_cards)\s*\(", cells[-1][0]):
            last["D6"] = step
            note = ("You fetched addresses/cards from the supervisor app, but apis.amazon.place_order needs address_id and payment_card_id from "
                    "Amazon itself:\naddresses = apis.amazon.show_addresses(access_token=amazon_token)\n"
                    "cards = apis.amazon.show_payment_cards(access_token=amazon_token)\nprint(addresses, cards)\n(the supervisor lists have no such ids).")
    # D8' spec re-read (validated: D8 within-task +0.29 disc / +0.39 val; docs share D1 is NOT predictive and is not nudged).
    # H1 already debounces byte-identical repeats; this catches a re-read written differently. Only reads still visible in the
    # 20-turn history window count (older reads have scrolled out, so re-reading them is legitimate).
    if note is None and len(cells) >= 2 and ok("D8", 4):
        kre = re.compile(r"""(?:show_api_doc|api_sig)\s*\(\s*(?:app_name\s*=\s*)?['"]([a-z_]+)['"]\s*,\s*(?:api_name\s*=\s*)?['"]([a-z_]+)['"]""")
        seen = set(k for c, _ in cells[-20:-1] for k in kre.findall(c))   # only reads still inside the 20-turn history window
        again = [k for k in kre.findall(cells[-1][0]) if k in seen]
        if again:
            last["D8"] = step; a_, f_ = again[0]
            note = (f"You already read the spec of {a_}.{f_} a few steps ago (it is still above in this conversation), so re-reading it costs a step. "
                    f"If you have the parameters, call apis.{a_}.{f_}(...) directly now; if it failed, the error message says which argument is wrong.")
    return prompt + ("\n\n[harness note] " + note if note else "")
