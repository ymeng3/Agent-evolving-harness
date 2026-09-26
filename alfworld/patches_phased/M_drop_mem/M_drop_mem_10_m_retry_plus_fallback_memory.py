HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Use a basic history-based approach to avoid repeating the last few actions
    recent_actions = state.get("recent_actions", [])
    for action in admissible:
        if action not in recent_actions:
            return action
    # If all admissible actions are recent, fallback to the first admissible one
    return admissible[0]

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Record last few actions to improve fallback decisions
    recent_actions = state.get("recent_actions", [])
    recent_actions.append(action)
    if len(recent_actions) > 5:
        recent_actions.pop(0)
    state["recent_actions"] = recent_actions