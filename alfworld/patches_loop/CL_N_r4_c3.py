HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "The chosen action was not applicable. Consider the context and previous actions to ensure your next choice aligns with the task goal. "
            "Please select an action from the admissible list that best fits the current observation."
        )
        return {"extra_instruction": extra_instruction}
    return None
