HISTORY_LENGTH = 8
TEMPERATURE = 0.6

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'invalid_actions' not in state:
        state['invalid_actions'] = 0
    if action not in next_observation:
        state['invalid_actions'] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    new_temperature = max(0.2, TEMPERATURE - 0.1 * state.get('invalid_actions', 0))
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None