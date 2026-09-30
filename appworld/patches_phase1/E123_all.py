SETUP_CODE = '''
def fetch_all(api_fn, page_key="page_index", max_pages=100, **kw):
    """Call a paginated list API repeatedly (page_index 0,1,2,...) until it returns nothing; returns the concatenated list."""
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

def _num(x):
    try: return float(x)
    except Exception: return None

def filter_products(items, max_price=None, min_price=None, min_rating=None, min_reviews=None):
    """Filter product dicts by price / rating / number of reviews (keys are looked up flexibly)."""
    out = []
    for p in items:
        price = _num(p.get("price"))
        rating = _num(p.get("rating") if p.get("rating") is not None else p.get("average_rating"))
        nrev = _num(p.get("review_count") if p.get("review_count") is not None else p.get("num_reviews", p.get("number_of_reviews")))
        if max_price is not None and (price is None or price > max_price): continue
        if min_price is not None and (price is None or price < min_price): continue
        if min_rating is not None and (rating is None or rating < min_rating): continue
        if min_reviews is not None and (nrev is None or nrev < min_reviews): continue
        out.append(p)
    return out
print("helpers ready: fetch_all, filter_products")

notes = {}
def remember(key, value):
    """Persist a task-relevant fact extracted from one app for use in another app."""
    notes[key] = value
    print("NOTE saved: " + str(key) + " = " + repr(value))
print("memory ready: notes, remember")

todo = []
def plan(items):
    """Register the concrete actions the task requires."""
    todo[:] = [[str(s), False] for s in items]
    print("PLAN: " + " | ".join("[" + str(i) + "] " + str(s) for i, s in enumerate(items)))
def done(i):
    todo[i][1] = True
    print("DONE: [" + str(i) + "] " + todo[i][0])
print("planner ready: plan, done")
'''


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    import re
    for m in re.finditer(r"NOTE saved: (.+?) = (.+)", next_observation):
        state.setdefault("notes", {})[m.group(1).strip()] = m.group(2).strip()[:200]
    m = re.search(r"PLAN: (.+)", next_observation)
    if m:
        state["todo"] = {int(a): [b.strip(), False] for a, b in re.findall(r"\[(\d+)\] ([^|]+)", m.group(1))}
    for a in re.findall(r"DONE: \[(\d+)\]", next_observation):
        if int(a) in state.get("todo", {}): state["todo"][int(a)][1] = True

def format_prompt(prompt: str, state: dict) -> str:
    state["_n"] = state.get("_n", 0) + 1
    if state["_n"] == 1:
        prompt += ("\n\nHelpers already defined in this session: fetch_all(api_fn, **kwargs) fetches ALL pages of a paginated list API; filter_products(items, max_price=, min_price=, min_rating=, min_reviews=) filters product dicts; "
                   "a persistent dict `notes` with remember(key, value) for facts you will need in another app or later; plan(list_of_actions) and done(i) to track the concrete actions the task requires. "
                   "Your FIRST cell must call plan([...]). Whenever the task asks for the best / highest-rated / cheapest / all / N items from a list, fetch ALL pages with fetch_all before choosing and filter by every stated constraint. "
                   "Call remember() for names, emails, phone numbers, items, quantities, amounts, dates, ids read in one app and needed elsewhere. Call done(i) after each planned action is achieved; complete the task only when all are done.")
    else:
        if state.get("notes"): prompt += "\n\nSaved notes so far: " + "; ".join(f"{k} = {v}" for k, v in list(state["notes"].items())[-12:])
        rem = [f"[{i}] {v[0]}" for i, v in sorted(state.get("todo", {}).items()) if not v[1]]
        if rem: prompt += "\n\nRemaining planned actions: " + "; ".join(rem)
    return prompt

def parse_action(response: str, admissible: list, state: dict) -> str:
    import re
    m = re.search(r"```python\s*(.*?)```", response, re.S) or re.search(r"```\s*(.*?)```", response, re.S)
    code = m.group(1).strip() if m else ""
    rem = [f"[{i}] {v[0]}" for i, v in sorted(state.get("todo", {}).items()) if not v[1]]
    if "complete_task" in code and rem and not state.get("_guarded"):
        state["_guarded"] = 1
        return 'print("Planned actions still open: ' + "; ".join(r.replace('"', "'") for r in rem) + '. Finish them, or call done(i) for each one already achieved, then complete the task.")'
    return code
