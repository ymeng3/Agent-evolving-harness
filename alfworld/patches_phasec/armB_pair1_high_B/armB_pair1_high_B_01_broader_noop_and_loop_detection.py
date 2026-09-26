import re, random, collections

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    state.setdefault("hist", []).append(act)
    if any(phrase in next_observation.lower() for phrase in ["nothing happens", "you can't do that", "unable to", "doesn't work"]):
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    loop_condition = noop.get(act, 0) >= 1 or (len(h) >= 2 and h[-1] == h[-2] == act)
    if act in admissible and loop_condition:
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a != act and a != "look" and a not in h[-4:]]
        if alt:
            return random.choice([a for a in alt if "take" in a] or alt)
    return act

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    alt = [a for a in admissible if "look" not in a and "inventory" not in a and a not in h[-4:]]
    return random.choice(alt) if alt else "look"