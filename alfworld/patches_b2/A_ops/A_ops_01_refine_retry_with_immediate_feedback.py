def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            f"Your previous action '{action}' was not admissible. "
            "Please carefully review the provided information and make sure to select your next action only from the admissible actions list. "
            "Pay close attention to the environment context and align your action choice with the task goal."
        )
        return {"extra_instruction": extra_instruction}
    return None