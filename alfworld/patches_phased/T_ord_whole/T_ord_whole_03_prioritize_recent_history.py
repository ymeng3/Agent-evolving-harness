HISTORY_LENGTH = 15
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Reduce temperature progressively for retry attempts to encourage more deterministic responses
    temperatures = [0.25, 0.15]
    extra_instruction = "Your last action wasn't valid. Please carefully select one of the admissible actions listed."
    if attempt <= len(temperatures):
        return {"extra_instruction": extra_instruction, "temperature": temperatures[attempt - 1]}
    return None