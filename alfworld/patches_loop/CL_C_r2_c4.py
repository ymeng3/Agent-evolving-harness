HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Please reconsider the context and ensure your action is one of the listed admissible actions.", "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": "Review your past observations and actions for guidance to choose a correct action.", "temperature": 0.2}
    return None
