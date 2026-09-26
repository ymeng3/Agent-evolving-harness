HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. It's crucial to choose from the listed admissible actions. Rethink and ensure your selection is valid."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None