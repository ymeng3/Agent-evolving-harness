HISTORY_LENGTH = 7
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "The selected action was not valid. Please choose an action from the admissible options given."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    elif attempt == 2:
        extra_instruction = "Last attempt was also invalid. Make sure to pick from the listed admissible actions carefully."
        return {"extra_instruction": extra_instruction, "temperature": 0.1}
    return None