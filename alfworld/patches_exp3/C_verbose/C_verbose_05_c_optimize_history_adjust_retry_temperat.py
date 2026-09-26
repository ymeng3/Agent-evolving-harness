HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Lower the temperature on retry to encourage more deterministic behavior
    if attempt == 1:
        return {"temperature": 0.2}
    elif attempt == 2:
        return {"temperature": 0.1}
    return None