HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Your last action wasn't valid. Please select an admissible action from the list provided."}
    elif attempt == 2:
        return {"extra_instruction": "Your previous attempts failed. Carefully choose an action from the admissible ones."}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' if available, otherwise choose the first admissible action
    preferred_action = 'look'
    if preferred_action in admissible:
        return preferred_action
    return admissible[0]