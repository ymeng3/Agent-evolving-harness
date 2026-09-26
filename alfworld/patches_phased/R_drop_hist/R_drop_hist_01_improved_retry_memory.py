TEMPERATURE = 0.5
HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Carefully review the admissible actions and select an appropriate one."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    recent_actions = state.setdefault("recent_actions", [])
    recent_actions.append(action)
    if len(recent_actions) > 10:
        recent_actions.pop(0)