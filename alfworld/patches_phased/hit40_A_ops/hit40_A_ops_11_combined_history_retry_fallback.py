HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "You must choose from the admissible actions.",
            "temperature": 0.5
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Carefully choose an admissible action now from the list above.",
            "temperature": 0.3
        }
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Select the first admissible action, preferring actions that move or observe
    for action in admissible:
        if "move" in action or "look" in action:
            return action
    return admissible[0] if admissible else 'look'