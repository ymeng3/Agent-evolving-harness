# Introduction of a memory cap alongside loop prevention.
# Tackles excessive memory growth by limiting stored action history to last 15.
# Counteracts 'ineffective action persistence' by preferring varied admissible actions.
import re, random, collections

HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    action_history = state.setdefault("hist", [])
    action_history.append(act)
    # Prune history to the last 15 actions
    if len(action_history) > 15:
        action_history.pop(0)
    if "nothing happens" in next_observation.lower(): 
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]]
        if alt: 
            varied_alternatives = [a for a in alt if 'fetch' in a or 'pick' in a or 'open' in a]
            return random.choice(varied_alternatives or alt)
    return act

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    varied_alt = [a for a in admissible if (a.startswith("go to") or a.startswith("open")) and a not in h]
    return random.choice(varied_alt) if varied_alt else "look"