TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"temperature": 0.2}
    return None