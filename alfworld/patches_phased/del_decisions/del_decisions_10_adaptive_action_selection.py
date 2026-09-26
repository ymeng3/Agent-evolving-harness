HISTORY_LENGTH = 8
TEMPERATURE = 0.45

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "The previous action was invalid. Analyze the options thoroughly before selecting."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        extra_instruction = "Focus closely on the admissible actions and choose the most suitable one."
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None