HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = ("Consider the current task requirements and recent observations to "
                             "select an action that aligns closely with achieving the task goal.")
        return {"extra_instruction": extra_instruction}
    return None
