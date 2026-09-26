HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust temperature based on retry attempt to balance exploration and exploitation
    if attempt == 1:
        return {"temperature": 0.6}  # slightly higher temperature for the first retry to allow more variation
    elif attempt == 2:
        return {"temperature": 0.4}  # lower temperature for the second retry to focus on precision
    return None