HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    prompt_advice = "Consider carefully why your previous action wasn't valid. "
    extra_instruction = prompt_advice + "Your next choice must be among the admissible actions provided."

    if attempt == 1:
        state['first_retry_response'] = response  # Store the first invalid response for debugging purposes
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None