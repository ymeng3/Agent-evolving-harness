HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on choosing an action listed as admissible. "
    if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
        admissible = [a for a in admissible if a != action]
        extra_instruction += "Avoid repeating actions excessively. "
        
    if attempt == 1:
        extra_instruction += f"Try a different approach; do not repeat the action: {action}."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction += "Make sure to analyze the context and choose a suitable action."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}

    return None