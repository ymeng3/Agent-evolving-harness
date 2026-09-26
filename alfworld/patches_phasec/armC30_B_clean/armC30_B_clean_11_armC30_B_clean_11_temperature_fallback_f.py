HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.7}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer 'look' action as a reasonable default in many circumstances.
    if 'look' in admissible:
        return 'look'
    # If 'look' is not available, choose any arbitrary valid action
    return admissible[0]