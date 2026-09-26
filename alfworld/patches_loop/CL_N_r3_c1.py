HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "You must select an action exactly from the admissible actions list provided."
        return {"extra_instruction": extra_instruction}
    return None
