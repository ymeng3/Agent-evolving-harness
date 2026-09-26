HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instructions = [
        "Your last action wasn't valid. Remember to focus on selecting one of the admissible actions listed.",
        "This is a critical moment. Please carefully analyze the situation and pick an admissible action.",
        "Your previous actions have led to this point. Reflect on what hasn't worked and choose wisely from the admissible actions."
    ]
    if attempt <= 3:
        return {"extra_instruction": extra_instructions[attempt - 1], "temperature": 0.3 - (attempt - 1) * 0.05}
    return None