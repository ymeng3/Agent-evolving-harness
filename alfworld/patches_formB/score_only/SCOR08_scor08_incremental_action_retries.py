HISTORY_LENGTH = 5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Increase the temperature incrementally with each retry attempt to promote different exploratory
    behavior from the model. This approach gradually increases the randomness of the model's output.
    """
    if attempt == 1:
        return {"temperature": 0.5}  # Slightly increase randomness on first retry
    elif attempt == 2:
        return {"temperature": 0.6}  # Further increase randomness on second retry
    return None