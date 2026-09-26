HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {
            "extra_instruction": "Re-evaluate the recent steps and choose a valid action from the list provided.",
            "temperature": 0.5
        }
    return None

