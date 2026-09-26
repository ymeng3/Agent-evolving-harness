HISTORY_LENGTH = 20

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {"extra_instruction": "Focus on completing the task as described and ensure actions are admissible.", "temperature": 0.3}
    return None
