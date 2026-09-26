HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_adjustment = 0.3 if attempt == 2 else 0.5 
    if attempt in [1, 2]:
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustment}
    return None