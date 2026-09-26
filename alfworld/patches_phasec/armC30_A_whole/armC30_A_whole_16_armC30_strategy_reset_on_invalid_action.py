HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # Reset part of the state if two invalid attempts have been made and retry with a lower temperature.
        if 'invalid_attempts' not in state:
            state['invalid_attempts'] = 0
        state['invalid_attempts'] += 1
        state.clear()  # Resetting state to avoid accumulation of invalid strategy.
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update invalid attempts count in state.
    if 'invalid_attempts' not in state:
        state['invalid_attempts'] = 0
    # Reset invalid attempts counter after a valid action.
    if action:
        state['invalid_attempts'] = 0