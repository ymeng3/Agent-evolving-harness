HISTORY_LENGTH = 10
TEMPERATURE = 0.4

import re, random, collections

def memory_update(state, observation, action, next_observation):
    m = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (m.group(1) if m else action).strip().lower()
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1
    # Track unsuccessful retries to detect persistent failures.
    state["retries"] = state.get("retries", 0) + (1 if state.get("retry_active") else 0)
    state["retry_active"] = False

def parse_action(response, admissible, state):
    m = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = m[-1].strip().lower() if m else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]]
        return random.choice([a for a in alt if a.startswith("go to")] or alt) if alt else act
    return act

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Please choose carefully from the admissible actions."
    if attempt <= 2:
        state["retry_active"] = True
        state["retries"] += 1  # Increment retry count
        return {"extra_instruction": extra_instruction, "temperature": max(0.2, TEMPERATURE - 0.1 * state["retries"])}
    return None

def choose_fallback(admissible, state):
    h = state.get("hist", [])
    alt = [a for a in admissible if a.startswith("go to") and a not in h]
    return random.choice(alt) if alt else "look"