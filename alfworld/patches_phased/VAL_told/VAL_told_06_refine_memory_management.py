HISTORY_LENGTH = 8

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Re-evaluate the situation and submit one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Maintain a list of actions executed to detect simple loops
    if 'actions_taken' not in state:
        state['actions_taken'] = []
    state['actions_taken'].append(action)
    # Limit the size of actions_taken list to avoid unnecessary memory usage
    if len(state['actions_taken']) > 20:
        state['actions_taken'].pop(0)