HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust temperature and guidance based on previous failures to encourage exploration
    if attempt == 1:
        return {
            "extra_instruction": "Try to reason carefully and choose from the provided admissible actions.",
            "temperature": 0.5  # Slightly increase temperature to allow more exploration.
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Focus on selecting actions distinctly different from previous attempts.",
            "temperature": 0.3  # Reduce temperature to encourage more deterministic responses post-exploration.
        }
    return None