import re

HISTORY_LENGTH = 7

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I); act = (m.group(1) if m else action).strip().lower()
    nxt = next_observation.lower()
    state.setdefault("visited", {}); state.setdefault("failed", 0)
    g = re.match(r"go to (.+)", act)
    if g:
        found = re.findall(r"you see (.*?)(?:\.|$)", nxt); state["visited"][g.group(1)] = (found[0][:80] if found else "nothing")
    o = re.match(r"open (.+)", act)
    if o:
        found = re.findall(r"you see (.*?)(?:\.|$)", nxt); state["visited"][o.group(1)] = (found[0][:80] if found else "nothing")
    t = re.match(r"take (.+?) from", act)
    if t and "nothing happens" not in nxt: state["holding"] = t.group(1)
    if act.startswith("put ") and "nothing happens" not in nxt: state["holding"] = None
    state["last_failed"] = "nothing happens" in nxt

def format_prompt(prompt, state):
    v = state.get("visited", {})
    note = ""
    if v: note += "\nMEMORY - receptacles already checked this episode (do not revisit unless you need them): " + "; ".join(f"{k}: {val}" for k, val in list(v.items())[-12:])
    if state.get("holding"): note += f"\nMEMORY - you are currently holding: {state['holding']}."
    if state.get("last_failed"): note += "\nNOTE - your last action did nothing; choose a different admissible action."
    
    # added instruction for prioritizing unvisited locations
    unvisited_locations = [loc for loc in state.get("admissible", []) if loc not in v]
    if unvisited_locations:
        note += f"\nNOTE - prioritize visiting unvisited locations: {', '.join(unvisited_locations)}."

    return prompt.replace("Now it's your turn to take an action.", note + "\nNow it's your turn to take an action.") if note else prompt

def parse_action(response, admissible, state):
    m = re.search(r"<action>(.*?)</action>", response, re.S | re.I)
    action = (m.group(1) if m else response).strip().lower()
    
    # Ensure action is admissible.
    if action not in admissible:
        # Prioritize unvisited actions if available.
        unvisited = [act for act in admissible if act not in state.get("visited", {})]
        if unvisited:
            return unvisited[0]

    return action if action in admissible else admissible[0]