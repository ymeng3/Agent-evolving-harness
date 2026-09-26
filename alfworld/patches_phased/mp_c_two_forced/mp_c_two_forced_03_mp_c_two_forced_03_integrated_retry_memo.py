HISTORY_LENGTH = 10
TEMPERATURE = 0.5

import re, collections

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    act = re.search(r"<action>(.*?)</action>", action, re.S | re.I)
    act = (act.group(1) if act else action).strip().lower()
    state.setdefault("hist", []).append(act)
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop", collections.Counter())[act] += 1

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    act = re.search(r"<action>(.*?)</action>", response, re.S | re.I)
    act = act.group(1).strip().lower() if act else response.strip().lower()[-30:]
    h = state.get("hist", [])
    noop = state.get("noop", {})
    if act in admissible and (noop.get(act, 0) >= 2 or (len(h) >= 2 and h[-1] == h[-2] == act)):
        state["loop_breaks"] = state.get("loop_breaks", 0) + 1
        alt = [a for a in admissible if a not in noop and a != act and a != "look" and a != "inventory" and a not in h[-6:]]
        if alt:
            return alt[0]
    return act