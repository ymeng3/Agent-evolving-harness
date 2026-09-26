HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Evaluate the context clues in your current observation to make a better decision. "
            "Ensure your action is aimed at progressing the task without repeating ineffective actions."
        )
        return {"extra_instruction": extra_instruction}
    return None
