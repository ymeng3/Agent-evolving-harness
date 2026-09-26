HISTORY_LENGTH = 5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # If the action is invalid, issue a re-query to improve the admissible-actions share and leverage success.
    if attempt < 2:
        extra_instruction = "Please ensure that your chosen action is among the admissible ones."
        temperature = 0.4  # Keep the original temperature for consistency.
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None