HISTORY_LENGTH = 10

TEMPERATURE = 0.2

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = "Ensure your selected action is one of the admissible actions. Double-check your reasoning."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None