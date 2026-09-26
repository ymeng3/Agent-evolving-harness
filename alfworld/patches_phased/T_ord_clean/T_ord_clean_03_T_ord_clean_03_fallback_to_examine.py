HISTORY_LENGTH = 10


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None


def choose_fallback(admissible: list[str], state: dict) -> str:
    """Choose 'examine' as a fallback action if it's admissible, otherwise fall back to 'look'."""
    return "examine" if "examine" in admissible else "look"