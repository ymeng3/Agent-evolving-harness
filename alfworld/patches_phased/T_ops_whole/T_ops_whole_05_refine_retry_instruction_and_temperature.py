HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = ("Your last action wasn't valid. Please carefully analyze the admissible actions "
                         "and choose the most sensible one for the current scene.")
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None