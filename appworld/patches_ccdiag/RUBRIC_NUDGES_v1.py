EDITS = [
    {"id": "e1", "capability": "ToolUse", "impl": "Prompt", "trigger": "after >= 6 cells, >= 50% of executed cells are api_docs calls (rubric D1); at most every 6 cells", "depends": [],
     "expected_effect": "fewer single-API doc cells; batched doc lookups", "side_effect_risk": "agent skips a doc it needed"},
    {"id": "e2", "capability": "Memory", "impl": "Prompt", "trigger": "the last cell repeated an api_docs call identical to an earlier cell (rubric D8)", "depends": ["e1"],
     "expected_effect": "no re-printing of docs already in context", "side_effect_risk": "none expected"},
    {"id": "e3", "capability": "Planning", "impl": "Prompt", "trigger": "the last two cells are identical up to literals and call a task API (rubric D2); at most every 3 cells", "depends": ["e1"],
     "expected_effect": "remaining items processed in one loop", "side_effect_risk": "a buggy loop fails all items at once"},
    {"id": "e4", "capability": "ToolUse", "impl": "Prompt", "trigger": "the last output reports an unexpected parameter / unknown API (rubric D4)", "depends": ["e1"],
     "expected_effect": "immediate correct re-call", "side_effect_risk": "none expected"},
    {"id": "e5", "capability": "ToolUse", "impl": "Prompt", "trigger": "supervisor addresses / payment cards fetched in an episode that uses amazon (rubric D6); once", "depends": ["e1"],
     "expected_effect": "amazon IDs fetched from amazon.show_addresses / show_payment_cards", "side_effect_risk": "none expected"},
    {"id": "e6", "capability": "Planning", "impl": "Prompt", "trigger": ">= 22 of 30 cells used: show cells left; <= 3 left: tell it to finish and call complete_task (rubric D7)", "depends": ["e1"],
     "expected_effect": "no end-of-budget waste; complete_task reached", "side_effect_risk": "premature completion"},
]


def e1_post_exec(code, out, state):
    state.setdefault("cells", []).append([code or "", (out or "")[:400]])


def e1_pre_call(prompt, state):
    state["step"] = state.get("step", -1) + 1
    cells = state.get("cells", [])
    if len(cells) >= 6 and state["step"] - state.get("e1_last", -99) >= 6:
        share = sum(1 for c, _ in cells if "api_docs" in c) / len(cells)
        if share >= 0.5:
            state["e1_last"] = state["step"]
            left = 30 - state["step"]
            return prompt + (f"\n\n[harness note] {int(share * 100)}% of your cells so far were documentation lookups and {left} cells remain. You may look up "
                             f"several APIs' docs in ONE cell (e.g. loop over the api names and print each spec), and you do not need to re-read the spec of an "
                             f"API whose parameters you already know.")
    return prompt


def e2_pre_call(prompt, state):
    import re
    cells = state.get("cells", [])
    if len(cells) < 2 or "api_docs" not in cells[-1][0]:
        return prompt
    key = " ".join(cells[-1][0].split())
    for k, (c, _) in enumerate(cells[:-1]):
        if " ".join(c.split()) == key:
            return prompt + (f"\n\n[harness note] You already ran this exact documentation call at cell {k}; its output is in the conversation above. "
                             f"Use it instead of re-reading; if a list was too long, print only the names or the one API you need.")
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
        left = 30 - state.get("step", 0)
        return prompt + (f"\n\n[harness note] Your last two cells did the same thing for different items. Put ALL remaining items in ONE loop in a single "
                         f"cell (collect the results in a list and print a compact summary). {left} cells remain.")
    return prompt


def e4_pre_call(prompt, state):
    import re
    cells = state.get("cells", [])
    if not cells:
        return prompt
    out = cells[-1][1]
    if re.search(r"Unexpected parameter|unexpected keyword|No API named|has no attribute|not a valid API", out, re.I):
        return prompt + ("\n\n[harness note] The last call used a parameter or API name that does not exist. Check the exact name and parameter list in the "
                         "spec you already have (for example, public search APIs such as amazon search_products take no access_token) and call it again correctly.")
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
    left = 30 - state.get("step", 0)
    if left <= 3:
        return prompt + (f"\n\n[harness note] Only {left} cell(s) left. Do the remaining state-changing call(s) now and call apis.supervisor.complete_task() "
                         f"(with answer=... if the task asks a question) in this cell if at all possible. Do not spend cells on docs or verification.")
    if left <= 8:
        return prompt + f"\n\n[harness note] {left} of 30 cells left. Plan the minimal remaining calls and batch them."
    return prompt
