def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Implements an adjusted retry policy with refined instructions and temperature settings.
    The instructions are more explicit and direct, while the temperature is adjusted to
    stabilize the model's action selection process for retries.
    """
    retries = {
        1: {
            "extra_instruction": " The previous action was invalid. Focus and select one action strictly from the admissible list provided.",
            "temperature": 0.35
        },
        2: {
            "extra_instruction": " Final attempt. Analyze carefully and choose only one action from the admissible list. Ensure it aligns with the task's requirements.",
            "temperature": 0.25
        }
    }
    return retries.get(attempt, None)