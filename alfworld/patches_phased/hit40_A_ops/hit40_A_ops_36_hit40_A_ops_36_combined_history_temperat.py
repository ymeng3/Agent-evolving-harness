HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction = "Your previous action was not admissible. Focus on selecting from the admissible actions."
    if attempt == 1:
        return {"extra_instruction": instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": instruction, "temperature": 0.7}
    return None