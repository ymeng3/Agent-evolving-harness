TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    base_instruction = "Ensure to choose an action from the admissible list."
    
    if attempt == 1:
        extra_instruction = base_instruction + " Be cautious about repeating actions excessively."
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            extra_instruction += " Avoid repeating the same action."
            admissible = [a for a in admissible if a != action]
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    
    elif attempt == 2:
        extra_instruction = base_instruction + " It's crucial to select an action that differs from previous attempts."
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
        return {"extra_instruction": extra_instruction, "temperature": 0.4}

    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to choose the least repeated admissible action as fallback
    action_counts = state.get('action_count', {})
    least_repeated_action = min((action for action in admissible), key=lambda action: action_counts.get(action, 0))
    return least_repeated_action if least_repeated_action in admissible else 'look'