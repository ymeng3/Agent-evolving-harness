HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Re-evaluate the situation and choose an appropriate action from the admissible actions provided."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = "Ensure your choice is valid. Select one of the admissible actions only."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None