HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please ensure that your next action is one of the admissible ones. Consult the list."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    return None