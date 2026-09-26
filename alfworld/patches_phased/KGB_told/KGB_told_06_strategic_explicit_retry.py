HISTORY_LENGTH = 8
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action wasn't valid. "
        "Carefully select one of the admissible actions listed. "
        "Consider the task and goals of your mission."
    )
    
    if attempt == 1:
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.25
        }
    
    return None