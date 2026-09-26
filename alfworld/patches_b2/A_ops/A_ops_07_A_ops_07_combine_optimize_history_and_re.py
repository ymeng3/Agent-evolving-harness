HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Introduce adaptive retry strategy with additional guidance
    if attempt == 1:
        return {
            "extra_instruction": "Your previous action was not admissible. Carefully choose an action from the admissible list.",
            "temperature": 0.4  # Slightly reduce temperature to encourage consistency
        }
    elif attempt == 2:
        return {
            "extra_instruction": "It's crucial to pick from the admissible actions now. Ensure your action choice aligns with these.",
            "temperature": 0.3  # Further reduce temperature for even more deterministic behavior
        }
    return None