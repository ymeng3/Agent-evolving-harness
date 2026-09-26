def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Refine retry strategy to make temperature adjustments more effective.
    if attempt == 1:
        return {
            "extra_instruction": "Your last action wasn't valid. Ensure you select from the admissible actions list.",
            "temperature": 0.35  # Slightly reduce temperature to balance exploration and determinism.
        }
    elif attempt == 2:
        return {
            "extra_instruction": "This is another incorrect choice. It's crucial to select from the admissible actions.",
            "temperature": 0.2  # Further reduce temperature to strongly encourage more deterministic behavior.
        }
    return None