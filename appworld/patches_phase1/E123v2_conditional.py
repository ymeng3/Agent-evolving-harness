SETUP_CODE = '''
def fetch_all(api_fn, page_key="page_index", max_pages=100, **kw):
    """Call a paginated list API for page_index 0,1,2,... until it returns nothing; returns all items."""
    items = []
    for i in range(max_pages):
        kw[page_key] = i
        r = api_fn(**kw)
        if isinstance(r, dict):
            lst = None
            for v in r.values():
                if isinstance(v, list):
                    lst = v
                    break
            r = lst if lst is not None else []
        if not r:
            break
        items.extend(r)
    return items
notes = {}
def remember(key, value):
    notes[key] = value
    print("NOTE saved: " + str(key) + " = " + repr(value))
print("helpers ready")
'''

def format_prompt(prompt: str, state: dict) -> str:
    state["_n"] = state.get("_n", 0) + 1
    if state["_n"] == 1:
        import re
        m = re.search(r"Task: (.*)", prompt, re.S); task = m.group(1).strip() if m else prompt[-400:]
        import re
        s = task.lower()
        apps = set()
        for a, pat in (("amazon", r"amazon"), ("gmail", r"gmail|e-?mail"), ("phone", r"\bphone\b|text message|voice message|alarm|contacts?"), ("venmo", r"venmo"),
                       ("spotify", r"spotify|song|playlist"), ("splitwise", r"splitwise"), ("simple_note", r"simple_note|\bnotes?\b"), ("file_system", r"file_system|file system|\bfile\b|documents"), ("todoist", r"todoist|to-?do list")):
            if re.search(pat, s): apps.add(a)
        state["_pag"] = bool(re.search(r"\b(highest|lowest|cheapest|best|top[- ]rated|most expensive|least expensive|all (my|the|of)|every|everything|any .{0,40}(with|that|whose)|under \$|below \$|over \d|at least \d|rating (over|above|of)|reviews?)\b", s))
        state["_cross"] = len(apps) >= 2
        clauses = [c.strip() for c in re.split(r"\b(?:and then|then)\b|;|\. ", s) if len(c.strip()) > 12]
        verbs = set(re.findall(r"\b(buy|order|send|return|request|pay|venmo|add|remove|update|change|set|delete|move|archive|label|relabel|reply|attach|download|upload|renew|cancel|post|play|create|schedule|befriend|invite|transfer|reset|import|migrate)\b", s))
        state["_multi"] = len(verbs) >= 2
        if state["_multi"] and len(clauses) < 2: clauses = [c.strip() for c in re.split(r"\b(?:and then|then|and)\b|;|\. ", s) if len(c.strip()) > 12]
        state["_clauses"] = [c[:80] for c in clauses][:4] if state["_multi"] else []
        state["_task"] = task[:300]
        extra = []
        if state["_pag"]: extra.append("This task selects or acts on items from a list under constraints: a helper fetch_all(api_fn, **kwargs) is defined that fetches ALL pages of a paginated list API (page_index 0,1,2,... until empty). Fetch all pages before comparing, counting or choosing, and apply every constraint stated in the task in code.")
        if state["_cross"]: extra.append("This task needs facts from one app inside another: a persistent dict `notes` and remember(key, value) are defined. When you read the needed names, emails, phone numbers, items, quantities, amounts, dates or ids, call remember() in the same cell and reuse the saved values later.")
        if state["_multi"]: extra.append("This task has several required actions: " + " | ".join(f"({i+1}) {c}" for i, c in enumerate(state["_clauses"])) + ". Do every one of them before calling apis.supervisor.complete_task().")
        if extra: prompt += "\n\n" + "\n".join(extra)
    else:
        if state.get("_cross") and state.get("notes"): prompt += "\n\nSaved notes: " + "; ".join(f"{k} = {v}" for k, v in list(state["notes"].items())[-10:])
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    import re
    for m in re.finditer(r"NOTE saved: (.+?) = (.+)", next_observation):
        state.setdefault("notes", {})[m.group(1).strip()] = m.group(2).strip()[:200]
    state["_mut"] = state.get("_mut", 0) + len(re.findall(r"apis\.(?!api_docs|supervisor)\w+\.(create|update|delete|send|add|remove|pay|post|reply|move|archive|change|reset|cancel|renew|upload|download|order|buy|set|transfer|book|import|attach)\w*\(", action)) if not next_observation.startswith("Execution failed") else state.get("_mut", 0)

def parse_action(response: str, admissible: list, state: dict) -> str:
    import re
    m = re.search(r"```python\s*(.*?)```", response, re.S) or re.search(r"```\s*(.*?)```", response, re.S)
    code = m.group(1).strip() if m else ""
    if state.get("_multi") and "complete_task" in code and not state.get("_guarded") and state.get("_mut", 0) < 2:
        state["_guarded"] = 1
        return 'print("Before completing: this task requires ' + str(len(state["_clauses"])) + ' actions (' + "; ".join(c.replace('"', "'") for c in state["_clauses"]) + '). So far fewer than two state-changing API calls succeeded. Complete the missing actions, then call complete_task.")'
    return code
