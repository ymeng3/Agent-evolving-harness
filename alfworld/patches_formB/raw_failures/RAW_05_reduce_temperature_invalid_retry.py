TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Lower the temperature each retry to potentially make the responses more deterministic.
    if attempt == 1:
        return {"temperature": 0.2}  # Reduce temperature on first retry
    if attempt == 2:
        return {"temperature": 0.1}  # Reduce temperature further on second retry
    return None