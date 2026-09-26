HISTORY_LENGTH = 8
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Modifies the retry strategy to adjust temperature based on invalid action attempts and to encourage exploration.
    """
    if attempt == 1:
        return {"temperature": 0.4}

    elif attempt == 2:
        return {"temperature": 0.3}
    
    return None