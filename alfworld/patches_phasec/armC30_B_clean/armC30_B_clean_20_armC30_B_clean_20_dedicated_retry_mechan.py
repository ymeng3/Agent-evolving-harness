HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = "Your last action wasn't valid. Consider the context and select from the given admissible actions."
    extra_instruction_2 = "Recall your past actions and observations before choosing an admissible action."
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction_1}
    elif attempt == 2:
        return {
            "extra_instruction": extra_instruction_2,
            "temperature": 0.3
        }
    return None