HISTORY_LENGTH = 10
TEMPERATURE = 0.4

import re, random, collections

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last attempt was invalid. Please make sure to select an action from the admissible list provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    state.setdefault("action_history", []).append(act)
    if "nothing happens" in next_observation.lower(): 
        state.setdefault("noop_counter", collections.Counter())[act] += 1

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("action_history", [])
    noop_counts = state.get("noop_counter", {})
    
    if act in admissible and (noop_counts.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        alt_actions = [a for a in admissible if a not in noop_counts and a != act and a not in h[-5:]]
        if alt_actions:
            return random.choice([a for a in alt_actions if a.startswith("go to")] or alt_actions)
    return act

def choose_fallback(admissible: list[str], state: dict) -> str:
    h = state.get("action_history", [])
    alt = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alt) if alt else "look"