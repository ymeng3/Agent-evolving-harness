HISTORY_LENGTH = 7

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = "Your last action wasn't valid. Please try to adhere strictly to the admissible actions given."
    extra_instruction_2 = "Focus on selecting a valid action from the admissible list only."
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction_1}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    fallback_priority = ['look', 'examine', 'check']
    for action in fallback_priority:
        if action in admissible:
            return action
    return admissible[0]