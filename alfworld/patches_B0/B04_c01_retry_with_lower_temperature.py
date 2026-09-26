TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Lower the temperature for the second attempt to encourage more deterministic behavior
    if attempt == 2:
        return {"temperature": 0.2}
    return None