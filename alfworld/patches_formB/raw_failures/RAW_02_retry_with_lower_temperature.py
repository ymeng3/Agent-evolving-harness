HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # The model often produces INVALID actions when it goes off-track in thinking
    # Lower the temperature on retry to encourage more deterministic outputs
    if attempt == 1:
        return {"extra_instruction": "Please ensure you select a valid, admissible action from the list.", "temperature": 0.2}
    elif attempt == 2:
        return {"extra_instruction": "Try selecting an admissible action from the options provided.", "temperature": 0.1}
    return None