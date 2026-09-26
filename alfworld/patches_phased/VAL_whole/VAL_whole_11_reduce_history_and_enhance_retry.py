HISTORY_LENGTH = 5
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = "Please choose an action from the admissible actions list. Think carefully."
    extra_instruction_2 = "Focus on selecting one of the explicitly listed actions. Make sure it's valid."

    if attempt == 1:
        return {"extra_instruction": extra_instruction_1, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_2, "temperature": 0.3}
    return None