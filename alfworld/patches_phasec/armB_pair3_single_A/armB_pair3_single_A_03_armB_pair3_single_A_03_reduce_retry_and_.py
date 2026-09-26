HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Implements a retry policy with focused retries.
    The first retry includes an extra instruction to select from the admissible actions 
    and to ensure action practicality. The second retry is removed to prevent excessive retry cycles.
    """
    if attempt == 1:
        return {
            "extra_instruction": " The previous action was not valid, please ensure you select an action from the admissible list and consider if it is practical in the current context.",
            "temperature": 0.3
        }
    return None