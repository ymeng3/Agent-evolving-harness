def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Dynamically adjust temperature based on attempt number to optimize model performance.
    if attempt == 1:
        return {
            "temperature": 0.6,
            "extra_instruction": (
                "Ensure the chosen action is admissible. Carefully reassess your reasoning."
            )
        }
    elif attempt == 2:
        return {
            "temperature": 0.2,
            "extra_instruction": (
                "It's vital to select from admissible actions now. Focus on refinements."
            )
        }
    return None