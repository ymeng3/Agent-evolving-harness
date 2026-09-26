HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action wasn't valid. Carefully analyze the current observation and history to choose an admissible action."
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        extra_instruction = "The action chosen is still not valid. Please focus on selecting one of the admissible actions listed and verify its suitability in the context."
        return {"extra_instruction": extra_instruction}
    return None