HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    def analyze_state():
        recent_failures = state.get("recent_invalid_actions", 0)
        if recent_failures >= 2:
            return "You've repeatedly chosen invalid actions."
        return "Your last action wasn't valid."
    
    extra_instruction = f"{analyze_state()} Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'invalid_action' in observation.lower():
        state['recent_invalid_actions'] = state.get('recent_invalid_actions', 0) + 1
    else:
        state['recent_invalid_actions'] = 0