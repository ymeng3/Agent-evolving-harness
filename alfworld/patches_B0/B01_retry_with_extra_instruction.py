def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Please choose an action from the list of admissible actions provided.", "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": "You must select an action explicitly from the admissible actions.", "temperature": 0.4}
    return None