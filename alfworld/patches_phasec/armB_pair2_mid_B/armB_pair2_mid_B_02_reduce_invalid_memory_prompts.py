import re

HISTORY_LENGTH = 10

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    nxt = next_observation.lower()
    state.setdefault("visited", {})
    state.setdefault("failed", 0)
    g = re.match(r"go to (.+)", act)
    if g:
        found = re.findall(r"you see (.*?)(?:\.|$)", nxt)
        state["visited"][g.group(1)] = (found[0][:80] if found else "nothing")
    o = re.match(r"open (.+)", act)
    if o:
        found = re.findall(r"you see (.*?)(?:\.|$)", nxt)
        state["visited"][o.group(1)] = (found[0][:80] if found else "nothing")
    t = re.match(r"take (.+?) from", act)
    if t and "nothing happens" not in nxt:
        state["holding"] = t.group(1)
    if act.startswith("put ") and "nothing happens" not in nxt:
        state["holding"] = None
    state["last_failed"] = "nothing happens" in nxt

def format_prompt(prompt, state):
    v = state.get("visited", {})
    note = ""
    if v:
        note += "\nMEMORY - receptacles already checked this episode: " + "; ".join(
            f"{k}: {val}" for k, val in list(v.items())[-12:])
    if state.get("holding"):
        note += f"\nMEMORY - you are currently holding: {state['holding']}."
    if state.get("last_failed"):
        note += "\nNOTE - your last action did nothing; try an alternative action."
    return prompt.replace("Now it's your turn to take an action.",
                          note + "\nNow it's your turn to take an action.") if note else prompt

def retry_policy(attempt, response, action, admissible, state):
    if attempt == 1 and state.get("last_failed"):
        return {"extra_instruction": "\nRemember to choose a new action that you haven't attempted with the same result. Focus on finding alternative solutions."}
    return None