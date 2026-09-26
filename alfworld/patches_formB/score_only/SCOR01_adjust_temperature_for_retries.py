TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """Adjusts the temperature for retries; provide additional guidance after failed attempts."""
    retry_settings = {
        "temperature": max(0.1, TEMPERATURE - (0.1 * attempt))
    }
    
    if attempt == 1:
        retry_settings["extra_instruction"] = "Consider revisiting the task goals and prioritizing actions closely associated with objects or locations mentioned in your previous observations."

    elif attempt == 2:
        retry_settings["extra_instruction"] = "Focus on actions that might help locate or manipulate objects relevant to your task. Re-evaluate any overlooked objects."

    return retry_settings