HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action wasn't valid. Carefully consider the context and select one of the admissible actions. Focus on minimizing unnecessary actions."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        extra_instruction = "This is your second attempt. Concentrate on the current observations, and choose the most sensible action from the admissible list."
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None