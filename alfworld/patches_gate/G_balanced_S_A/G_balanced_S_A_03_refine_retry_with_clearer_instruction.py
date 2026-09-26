def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous choice was not valid. Make sure to select an action from the given admissible actions."
            " Carefully reason through the current situation and the provided description."
            " Re-examine the current observation and details about the task before selecting."
        )
        return {"extra_instruction": extra_instruction}
    return None