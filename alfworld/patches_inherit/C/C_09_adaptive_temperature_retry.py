HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    corrective_instruction = "Your last action wasn't valid. Please ensure to pick from the given admissible actions."
    # Implement adaptive temperature: decrease temperature further on consecutive failures.
    temperature = 0.4 - 0.1 * attempt
    if attempt <= 2:
        return {"extra_instruction": corrective_instruction, "temperature": max(0.1, temperature)}
    return None