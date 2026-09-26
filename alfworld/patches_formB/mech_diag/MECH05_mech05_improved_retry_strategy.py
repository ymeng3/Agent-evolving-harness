def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # On first invalid attempt, ask the model to clearly identify the action.
    if attempt == 1:
        return {"extra_instruction": "Ensure the action is specified clearly and follows the format.", "temperature": 0.5}
    # On second attempt, emphasize admissibility and lower temperature for more confident choice.
    elif attempt == 2:
        return {"extra_instruction": "Choose only a clear and admissible action from the given options.", "temperature": 0.3}
    # Accept as invalid at the third attempt.
    return None