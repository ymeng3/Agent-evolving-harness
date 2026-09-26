HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize non-destructive actions if available
    for action in admissible:
        if "look" in action or "examine" in action:
            return action
    # Default to the first admissible action if no non-destructive actions are found
    return admissible[0] if admissible else "look"