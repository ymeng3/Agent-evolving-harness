HISTORY_LENGTH = 8

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Your last action was invalid. Focus on selecting one of the admissible actions.",
            "temperature": 0.35
        }
    elif attempt == 2:
        return {
            "extra_instruction": "It's crucial to choose from the admissible actions now.",
            "temperature": 0.3
        }
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # If no valid action is found after retries, choose a default sensible action.
    common_fallbacks = ['look', 'close fridge', 'open door']
    for fallback in common_fallbacks:
        if fallback in admissible:
            return fallback
    return 'look'