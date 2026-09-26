HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action was not valid. Please carefully select one of the following admissible actions."
    if attempt <= 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    return None