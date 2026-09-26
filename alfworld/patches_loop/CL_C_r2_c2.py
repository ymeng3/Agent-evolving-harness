HISTORY_LENGTH = 5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt <= 2:
        return {
            "extra_instruction": "The previous action was invalid. Please ensure the action is one of the admissible actions for this step.",
            "temperature": 0.4
        }
    return None
