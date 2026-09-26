TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {
            "extra_instruction": "Please ensure that the action is one of the admissible actions listed above.",
            "temperature": 0.2
        }
    return None