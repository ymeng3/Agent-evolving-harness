HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_changes = [0.6, 0.7]
    if attempt in [1, 2]:
        return {"extra_instruction": extra_instruction, "temperature": temperature_changes[attempt - 1]}
    return None