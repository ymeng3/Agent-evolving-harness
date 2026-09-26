HISTORY_LENGTH = 15
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instructions = [
        "Your last action wasn't valid. Carefully pick one from the admissible actions.",
        "Your action is still invalid. Choose one of the admissible actions rigidly."
    ]
    if attempt <= 2:
        return {"extra_instruction": instructions[attempt - 1]}
    return None