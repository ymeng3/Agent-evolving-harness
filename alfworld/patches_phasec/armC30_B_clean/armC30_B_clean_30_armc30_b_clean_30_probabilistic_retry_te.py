HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    import random

    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": random.uniform(0.4, 0.6)}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None