HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    feedback_messages = [
        "Initial invalid action. Consider the list of admissible actions carefully.",
        "Second invalid attempt. Try to closely match one of the admissible actions.",
        "Final attempt. Make sure to choose a valid action from the list provided."
    ]
    
    if attempt < 3:
        return {
            "extra_instruction": feedback_messages[attempt - 1],
            "temperature": max(0.2, TEMPERATURE - 0.1 * attempt)
        }
    return None