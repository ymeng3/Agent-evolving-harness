HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Please ensure your action is one of the admissible actions.", "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": "Try again to pick an admissible action.", "temperature": 0.6}
    return None
