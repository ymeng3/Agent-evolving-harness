HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Double-check your reasoning and ensure the action aligns with the admissible list.", "temperature": 0.4}
    return None
