HISTORY_LENGTH = 5
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize fallback action 'look' unless it's unavailable, then choose the first admissible action.
    return 'look' if 'look' in admissible else admissible[0]