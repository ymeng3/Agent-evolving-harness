HISTORY_LENGTH = 10

TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Use the state dictionary to remember the history of invalid attempts
    if "invalid_attempts" not in state:
        state["invalid_attempts"] = 0

    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."

    if attempt == 1:
        state["invalid_attempts"] += 1
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        state["invalid_attempts"] += 1
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Reset invalid attempts after a valid action
    state["invalid_attempts"] = 0