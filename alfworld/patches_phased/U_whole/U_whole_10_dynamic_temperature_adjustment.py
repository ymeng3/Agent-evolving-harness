HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    # Choose temperature dynamically based on attempt number
    temperature = 0.3 - (0.1 * attempt)
    if attempt <= 2:
        return {"extra_instruction": extra_instruction, "temperature": max(0.1, temperature)}
    return None