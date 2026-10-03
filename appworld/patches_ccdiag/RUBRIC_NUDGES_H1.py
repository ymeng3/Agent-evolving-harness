EDITS = [
    {"id": "e1", "capability": "ToolUse", "impl": "Prompt", "trigger": "after >= 6 cells, >= 50% of executed cells are api_docs / api_index calls (rubric D1); at most every 6 cells", "depends": [],
     "expected_effect": "fewer single-API doc cells; batched lookups", "side_effect_risk": "agent skips a doc it needed"},
    {"id": "e3", "capability": "Planning", "impl": "Prompt", "trigger": "the last two cells are identical up to literals and call a task API (rubric D2); at most every 3 cells", "depends": ["e1"],
     "expected_effect": "remaining items processed in one loop", "side_effect_risk": "a buggy loop fails all items at once"},
    {"id": "e5", "capability": "ToolUse", "impl": "Prompt", "trigger": "supervisor addresses / payment cards fetched in an episode that uses amazon (rubric D6); once", "depends": ["e1"],
     "expected_effect": "amazon IDs fetched from amazon.show_addresses / show_payment_cards", "side_effect_risk": "none expected"},
    {"id": "e6", "capability": "Planning", "impl": "Prompt", "trigger": "<= 3 of 30 cells left and complete_task not called (rubric D7)", "depends": ["e1"],
     "expected_effect": "no end-of-budget waste; complete_task reached", "side_effect_risk": "premature completion"},
]
# H1 already covers: duplicate docs calls (debounced), API misuse (signature hint on parameter errors), step count (shown every output).


def e1_post_exec(code, out, state):
    state.setdefault("cells", []).append([code or "", (out or "")[:400]])


def e1_pre_call(prompt, state):
    state["step"] = state.get("step", -1) + 1
    cells = state.get("cells", [])
    if len(cells) >= 6 and state["step"] - state.get("e1_last", -99) >= 6:
        share = sum(1 for c, _ in cells if "api_docs" in c or "api_index" in c) / len(cells)
        if share >= 0.5:
            state["e1_last"] = state["step"]
            return prompt + (f"\n\n[harness note] {int(share * 100)}% of your cells so far were documentation lookups. Look up several APIs in ONE cell "
                             f"(or use api_index(app_name) once per app), and call APIs whose parameters you already know without re-reading their spec.")
    return prompt


def e3_pre_call(prompt, state):
    import re
    cells = state.get("cells", [])
    if len(cells) < 2 or state.get("step", 0) - state.get("e3_last", -99) < 3:
        return prompt
    lit = re.compile(r"""("([^"\\]|\\.)*"|'([^'\\]|\\.)*'|\b\d+(\.\d+)?\b)""")
    norm = lambda s: " ".join(lit.sub("#", s).split())
    a, b = cells[-2][0], cells[-1][0]
    calls = re.findall(r"apis\.([a-z_]+)\.([a-z_]+)\s*\(", b)
    if a != b and norm(a) == norm(b) and any(app != "api_docs" for app, _ in calls):
        state["e3_last"] = state.get("step", 0)
        return prompt + ("\n\n[harness note] Your last two cells did the same thing for different items. Put ALL remaining items in ONE loop in a single "
                         "cell (collect the results in a list and print a compact summary).")
    return prompt


def e5_pre_call(prompt, state):
    import re
    cells = state.get("cells", [])
    if not cells or state.get("e5_done"):
        return prompt
    uses_amazon = any("apis.amazon." in c for c, _ in cells)
    if uses_amazon and re.search(r"apis\.supervisor\.(show_addresses|show_payment_cards)\s*\(", cells[-1][0]):
        state["e5_done"] = True
        return prompt + ("\n\n[harness note] apis.amazon.place_order needs an address_id and a payment_card_id from apis.amazon.show_addresses and "
                         "apis.amazon.show_payment_cards (the supervisor lists have no IDs). Fetch both in one cell.")
    return prompt


def e6_pre_call(prompt, state):
    import re
    left = 30 - state.get("step", 0)
    done = any(re.search(r"apis\.supervisor\.complete_task\s*\(", c) for c, _ in state.get("cells", []))
    if left <= 3 and not done:
        return prompt + (f"\n\n[harness note] Only {left} step(s) left. Do the remaining state-changing call(s) now and call apis.supervisor.complete_task() "
                         f"(with answer=... if the task asks a question) in this step if at all possible. Do not spend steps on docs or verification.")
    return prompt
