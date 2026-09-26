HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        previous_steps_context = "Previous steps attempted, consider alternative actions."
        extra_instruction = f"{previous_steps_context} Please choose a different approach."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = "It is critical to adhere to admissible actions. Re-evaluate the options available."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None