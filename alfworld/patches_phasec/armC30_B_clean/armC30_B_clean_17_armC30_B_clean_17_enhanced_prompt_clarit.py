HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action wasn't valid. Please ensure clarity in your reasoning by referencing specific aspects of your "
        "current observation and focusing on selecting one of the admissible actions listed."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None