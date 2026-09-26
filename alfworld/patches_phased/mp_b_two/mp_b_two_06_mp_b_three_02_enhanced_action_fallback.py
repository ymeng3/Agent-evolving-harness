HISTORY_LENGTH = 10
TEMPERATURE = 0.5

import re, random

def memory_update(state, observation, action, next_observation):
    def extract_action(action_text):
        m = re.search(r"<action>(.*?)</action>", action_text, re.S | re.I)
        return (m.group(1) if m else action_text).strip().lower()
    
    act = extract_action(action)
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", {})[act] = state["noop"].get(act, 0) + 1

def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a not in h[-6:]]
        if alt:
            return random.choice([a for a in alt if a not in ["look", "inventory"]] or alt)
    return act

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    filtered_admissible = [a for a in admissible if a not in h[-3:]]
    fallback_options = [a for a in filtered_admissible if a.startswith("go to")]
    return random.choice(fallback_options) if fallback_options else "look"