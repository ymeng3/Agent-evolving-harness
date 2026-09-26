HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to choose the most relevant fallback action instead of just 'look'
    # Prioritize any action that involves 'inspect' or 'look' to gather more information
    reasoning_keywords = ["inspect", "look", "check", "see"]
    for action in admissible:
        if any(keyword in action for keyword in reasoning_keywords):
            return action
    # Default to the first admissible action as the last resort if no reasoning actions are found
    return admissible[0] if admissible else 'look'