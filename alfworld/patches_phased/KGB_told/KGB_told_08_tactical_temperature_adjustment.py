HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_adjustments = [0.5, 0.7, 0.85]  # Define a temperature adjustment sequence

    if attempt in [1, 2]:
        return {
            "extra_instruction": extra_instruction,
            "temperature": temperature_adjustments[attempt-1]  # Adjust temperature on retry attempts
        }
    
    return None