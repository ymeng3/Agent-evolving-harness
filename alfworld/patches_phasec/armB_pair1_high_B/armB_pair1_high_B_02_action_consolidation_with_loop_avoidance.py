import re, random, collections

HISTORY_LENGTH = 10

def memory_update(state, observation, action, next_observation):
    def extract_action(content):
        m = re.search(r"<action>(.*?)</action>", content, re.S | re.I)
        return (m.group(1) if m else content).strip().lower()
    
    act = extract_action(action)
    state.setdefault("hist", []).append(act)
    
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    def extract_actions(response_text):
        return re.findall(r"<action>(.*?)</action>", response_text, re.S | re.I)
    
    m = extract_actions(response)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]]
        if alt:
            return random.choice([a for a in alt if a.startswith("go to")] or alt)
    return act

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    alt = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alt) if alt else "look"