HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    state['action_count'][action] = state['action_count'].get(action, 0) + 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction = " Your previous action was invalid."
    
    if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
        admissible = [a for a in admissible if a != action]
        instruction += " Avoid repeating the same action too often. "
    
    instruction += " Consider the context and choose your action from the admissible options provided."

    if attempt == 1:
        return {"extra_instruction": instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None