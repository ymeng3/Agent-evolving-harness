HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. "
        "Think through the current state and your previous steps."
    )
    extra_instruction_2 = (
        "This is your final retry. Choose an action from the admissible list. "
        "Consider every detail in the observation and action choices carefully."
    )
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction_1, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_2, "temperature": 0.2}
    return None