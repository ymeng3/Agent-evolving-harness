HISTORY_LENGTH = 8
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    state.setdefault('invalid_attempts', 0)
    state['invalid_attempts'] += 1
    
    extra_instruction = (
        "Your previously chosen action was invalid. Carefully read "
        "the observation and admissible actions again to select the correct action."
    )

    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_action'] = action
    if 'look' in action.lower():
        state['last_look'] = next_observation