HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = f"Your last action '{action}' wasn't valid. Focus on selecting one of these admissible actions: {admissible}. Ensure to choose one that directly advances your task objectives."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None