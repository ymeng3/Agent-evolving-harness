HISTORY_LENGTH = 5
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Be especially cautious to pick an action listed as admissible."
    if attempt == 1:
        if 'action_count' in state and action in state['action_count'] and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            extra_instruction += " Avoid repeating actions excessively. Choose a different action."
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        if 'action_count' in state and action in state['action_count'] and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            extra_instruction += " Avoid repeating actions excessively. Choose a different action."
        return {"extra_instruction": extra_instruction, "temperature": 0.7}
    return None