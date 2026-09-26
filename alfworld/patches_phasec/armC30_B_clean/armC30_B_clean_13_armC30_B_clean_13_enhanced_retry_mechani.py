HISTORY_LENGTH = 10
TEMPERATURE = 0.7

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    base_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if 'retry_attempts' not in state:
        state['retry_attempts'] = 0

    # Increment retry attempt count in the state
    state['retry_attempts'] += 1

    # Use a more instructive message and a higher temperature for diversity on the first retry,
    # and further guidance on the second retry.
    if attempt == 1:
        return {
            "extra_instruction": f"{base_instruction} Carefully analyze the situation before selecting.",
            "temperature": TEMPERATURE
        }
    elif attempt == 2:
        return {
            "extra_instruction": f"{base_instruction} Consider what you observed and refer to past successful actions.",
            "temperature": TEMPERATURE
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Resetting the retry attempts on a successful action.
    state['retry_attempts'] = 0