HISTORY_LENGTH = 10

TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        new_temperature = TEMPERATURE - 0.1  # Reduce temperature to improve response consistency
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None
