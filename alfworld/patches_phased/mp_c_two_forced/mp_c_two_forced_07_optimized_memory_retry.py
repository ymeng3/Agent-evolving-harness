HISTORY_LENGTH = 10
TEMPERATURE = 0.5

import re, random, collections

def memory_update(state, observation, action, next_observation):
    # Inherited from Archive Entry B
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response, admissible, state):
    # Inspired by Archive Entry B but with simplification
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    return act if act in admissible else random.choice(admissible)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Modified from Archive Entry A with adjusted temperature scaling
    extra_instruction = "Please ensure your action is one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def choose_fallback(admissible, state):
    alt = [a for a in admissible if a.startswith("go to")]
    return random.choice(alt) if alt else "look"