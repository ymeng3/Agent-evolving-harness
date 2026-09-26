HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        extra_instruction = "It's important to select one of the admissible actions carefully."
        temperature_decrease = 0.2  # more deterministic output
        return {"extra_instruction": extra_instruction, "temperature": temperature_decrease}
    return None
