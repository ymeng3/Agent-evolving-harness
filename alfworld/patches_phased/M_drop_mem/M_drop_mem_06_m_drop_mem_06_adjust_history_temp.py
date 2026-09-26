HISTORY_LENGTH = 15
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Re-evaluate the current situation and prioritize choosing from the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None