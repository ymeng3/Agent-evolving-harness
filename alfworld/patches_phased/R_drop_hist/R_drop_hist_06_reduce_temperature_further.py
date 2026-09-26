TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The previous action was invalid. Make sure to choose from the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.15}
    return None