HISTORY_LENGTH = 15
TEMPERATURE = 0.4

import collections, re, random

def memory_update(state, observation, action, next_observation):
    action_text = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (action_text.group(1) if action_text else action).strip().lower()
    state.setdefault("hist", []).append((act, observation))
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1
    if len(state["hist"]) > 15:
        state["hist"].pop(0)

def parse_action(response, admissible, state):
    actions = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    act = actions[-1].strip().lower() if actions else response.strip().lower()[-30:]
    history = state.get("hist", [])
    noop_count = state.get("noop", {}).get(act, 0)

    if act in admissible and (noop_count >= 2 or (len(history) >= 4 and all(act == h[0] for h in history[-4:]))):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alternatives = [a for a in admissible if a not in state.get("noop", {}) and a != act and a not in [h[0] for h in history[-6:]]]
        return random.choice([a for a in alternatives if a.startswith("go to")] or alternatives)
    
    return act

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 3:
        return {
            "extra_instruction": "Please select an action from the admissible actions.",
            "temperature": max(0.1, 0.4 - 0.1 * attempt)
        }
    return None

def choose_fallback(admissible, state):
    recent = {h[0] for h in state.get("hist", [])[-6:]}
    candidates = [a for a in admissible if a.startswith("go to") and a not in recent]
    return random.choice(candidates) if candidates else "look"