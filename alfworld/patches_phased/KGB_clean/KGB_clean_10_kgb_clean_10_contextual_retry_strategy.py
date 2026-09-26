HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_1 = (
        "Your last action wasn't valid. Please select one of the admissible actions listed."
    )
    extra_instruction_2 = (
        "This action is still not valid. Double-check the admissible actions and make a thoughtful selection."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction_1, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_2, "temperature": 0.6}
    return None