# Increase history for better context
HISTORY_LENGTH = 15
# Increase temperature for increased exploration and adaptability
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Basic extra instruction for retries
    extra_instruction = "Your last action was not valid. Select one of the admissible actions only."
    if attempt == 1:
        # Provide guidance message for first attempt
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        # On second retry try to enhance focus and model flexibility
        return {"extra_instruction": extra_instruction + " You must ensure the action is sensible given the task context."}
    return None