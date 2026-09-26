HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust temperature and guidance based on previous failures to encourage exploration
    if attempt == 1:
        return {
            "extra_instruction": "Think again, and ensure your chosen action is from the admissible list.",
            "temperature": 0.6  # Increase temperature to encourage exploration and diverse actions.
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Make sure to reason clearly and avoid repeating previous actions.",
            "temperature": 0.3  # Lower temperature to concentrate on more deterministic selections.
        }
    return None