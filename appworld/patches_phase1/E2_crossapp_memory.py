SETUP_CODE = '''
notes = {}
def remember(key, value):
    """Persist a task-relevant fact extracted from one app for use in another app."""
    notes[key] = value
    print("NOTE saved: " + str(key) + " = " + repr(value))
print("memory ready: notes, remember")
'''

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    import re
    for m in re.finditer(r"NOTE saved: (.+?) = (.+)", next_observation):
        state.setdefault("notes", {})[m.group(1).strip()] = m.group(2).strip()[:200]

def format_prompt(prompt: str, state: dict) -> str:
    state["_n"] = state.get("_n", 0) + 1
    if state["_n"] == 1:
        prompt += ("\n\nA persistent dict `notes` and a function remember(key, value) exist in this session. Whenever you read task-relevant facts in one app "
                   "(names, emails, phone numbers, item names and quantities, amounts, dates, times, ids, addresses) that you will need in another app or a later step, "
                   "call remember(key, value) in the same cell. Use the saved values instead of re-deriving them.")
    elif state.get("notes"):
        prompt += "\n\nSaved notes so far: " + "; ".join(f"{k} = {v}" for k, v in list(state["notes"].items())[-12:])
    return prompt
