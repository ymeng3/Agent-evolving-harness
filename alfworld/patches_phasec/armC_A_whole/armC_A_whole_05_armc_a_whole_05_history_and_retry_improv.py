HISTORY_LENGTH = 15
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    encouragement = "Re-evaluate the situation. Consider the current context and choose an action from the options provided."
    if attempt == 1:
        return {"extra_instruction": encouragement, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": "Ensure your action aligns with one of the admissible actions.", "temperature": 0.25}
    return None