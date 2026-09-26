HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_adjustment = 0.4 if attempt == 1 else 0.6
    return {
        "extra_instruction": extra_instruction,
        "temperature": temperature_adjustment
    }