HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Refining the wording of the extra instruction to improve clarity and emphasis on valid action selection.
    if attempt == 1:
        return {"extra_instruction": "The action you chose was invalid. Carefully select one of the admissible actions provided."}
    elif attempt == 2:
        return {"extra_instruction": "Your last action attempt was also invalid. Ensure you choose strictly from the given admissible actions list."}
    return None