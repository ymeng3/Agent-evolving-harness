HISTORY_LENGTH = 10
TEMPERATURE = 0.45

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instructions = [
        "Your last action wasn't valid. Review the admissible actions carefully and choose one.",
        "Your last action wasn't valid again. Pay closer attention to the admissible actions.",
    ]
    if attempt in [1, 2]:
        extra_instruction = instructions[attempt - 1]
        temperature = 0.25 if attempt == 2 else 0.35
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None