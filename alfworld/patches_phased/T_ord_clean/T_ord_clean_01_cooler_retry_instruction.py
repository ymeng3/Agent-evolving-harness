HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_at_1 = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. "
        "Consider actions that might be more appropriate for the current observation."
    )
    extra_instruction_at_2 = (
        "Please choose more carefully among the given admissible actions. "
        "Look closely at your surroundings and the context of the task."
    )
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction_at_1}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_at_2}
    
    return None