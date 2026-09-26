HISTORY_LENGTH = 8
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Compose retry strategy with history length optimization
    if attempt == 1:
        # First retry with emphasis on admissible actions and slight temperature change
        instruction = (
            "Previous action was invalid. Focus on selecting from the admissible actions."
            " This will ensure more progress towards the task completion."
        )
        return {"extra_instruction": instruction, "temperature": 0.5}
    elif attempt == 2:
        # Second retry with stronger emphasis and safer temperature decrease
        instruction = (
            "It is crucial to select from the admissible list to proceed."
            " Consider all recent observations to make an informed decision."
        )
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None