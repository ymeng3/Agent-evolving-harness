HISTORY_LENGTH = 8
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Carefully choose one of the admissible actions."
    adjustment = {"extra_instruction": extra_instruction}
    
    if attempt == 1:
        adjustment["temperature"] = 0.4
    elif attempt == 2:
        adjustment["temperature"] = 0.3
    else:
        return None

    if "invalid_action_count" not in state:
        state["invalid_action_count"] = 0
    
    state["invalid_action_count"] += 1
    
    if state["invalid_action_count"] > 2:
        adjustment["extra_instruction"] += " Consider revisiting earlier observations to inform your choice."

    return adjustment

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "memory" not in state:
        state["memory"] = []
    
    state["memory"].append((observation, action))
    
    if len(state["memory"]) > HISTORY_LENGTH:
        state["memory"].pop(0)
    
    if action not in state:
        state[action] = 0
    state[action] += 1

    if state[action] > 3:
        state["memory"].clear()
        state[action] = 0