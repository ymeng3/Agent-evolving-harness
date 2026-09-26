HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_increase = lambda attempt: attempt * 0.1 if attempt <= 2 else 0.2
    if attempt <= 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4 + temperature_increase(attempt)}
    return None