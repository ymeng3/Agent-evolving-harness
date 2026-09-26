HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "The last action was invalid. Carefully review the admissible actions."
        temperature = 0.5
    elif attempt == 2:
        extra_instruction = "You still have selected an invalid action. Focus solely on the admissible actions this time."
        temperature = 0.7
    else:
        return None
    return {"extra_instruction": extra_instruction, "temperature": temperature}