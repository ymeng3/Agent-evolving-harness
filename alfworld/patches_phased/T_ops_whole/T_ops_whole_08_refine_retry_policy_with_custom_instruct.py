HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "The previous action was invalid. Carefully consider the context and choose from valid actions listed below.",
            "temperature": 0.35
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Once again, your chosen action was not valid. The valid actions are provided below. Please select the most appropriate one.",
            "temperature": 0.25
        }
    return None