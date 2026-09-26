HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if 'retry_count' not in state:
        state['retry_count'] = 0

    state['retry_count'] += 1
    extra_instruction = "Your previous action was invalid. Make sure to choose one of the admissible actions available."

    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()

    # Add the current observation to the visited set to avoid loops
    state['visited'].add(observation)

    # Reset retry count after a successful new action
    state['retry_count'] = 0