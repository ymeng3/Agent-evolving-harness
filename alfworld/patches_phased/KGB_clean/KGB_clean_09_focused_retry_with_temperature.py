HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action wasn't valid. Focus on selecting an admissible action from the list provided."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        extra_instruction = "Your previous attempts were invalid. Carefully review the admissible actions and choose one."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None