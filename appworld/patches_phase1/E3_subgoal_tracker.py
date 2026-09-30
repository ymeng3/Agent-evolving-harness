SETUP_CODE = '''
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
    m = re.search(r"PLAN: (.+)", next_observation)
    if m:
        state["todo"] = {int(a): [b.strip(), False] for a, b in re.findall(r"\[(\d+)\] ([^|]+)", m.group(1))}
    for a in re.findall(r"DONE: \[(\d+)\]", next_observation):
        if int(a) in state.get("todo", {}): state["todo"][int(a)][1] = True

def format_prompt(prompt: str, state: dict) -> str:
    state["_n"] = state.get("_n", 0) + 1
    if state["_n"] == 1:
        prompt += ("\n\nFunctions plan(list_of_actions) and done(i) exist in this session. Your FIRST cell must call plan([...]) listing every concrete action the task requires "
                   "(one entry per distinct app action or deliverable, e.g. 'return the order', 'venmo the refund to roommate'). After each action is actually achieved, call done(i). "
                   "Only call apis.supervisor.complete_task() when every planned action is done.")
    else:
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
