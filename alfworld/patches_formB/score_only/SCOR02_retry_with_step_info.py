def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:  # Allow one retry
        extra_instruction = f"Please note that your previous action '{action}' was not valid. Re-evaluate considering the current history and task. It's important that the chosen action matches one of the admissible actions."
        return {"extra_instruction": extra_instruction}
    return None