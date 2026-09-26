HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Be sure to choose an action from the admissible list.", "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": "Focus on selecting a valid action carefully this time.", "temperature": 0.2}
    else:
        return None
