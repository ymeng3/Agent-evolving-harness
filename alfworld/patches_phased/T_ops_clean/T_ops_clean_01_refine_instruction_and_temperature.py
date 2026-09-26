HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = "Your last action wasn't valid. Ensure you choose a correct action from the given list of admissible actions."
    extra_instruction_2 = "Please carefully check the previous reasoning and focus specifically on the admissible actions."

    if attempt == 1:
        return {"extra_instruction": extra_instruction_1, "temperature": 0.45}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_2, "temperature": 0.5}
    
    return None