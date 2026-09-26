def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Provide different instructions based on attempt count to enrich the guidance during retries
    if attempt == 1:
        # First retry, encourage focused reasoning and adherence to admissible actions
        return {
            "extra_instruction": (
                "Reflect carefully on the environment and your task. "
                "Pick actions strictly from the admissible list provided. "
                "Consider your reasoning in choosing an action."
            ),
            "temperature": 0.5
        }
    elif attempt == 2:
        # Second retry, highlight critical aspects of decision-making
        return {
            "extra_instruction": (
                "Ensure your chosen action fully aligns with the admissible list. "
                "Focus intensely on the goals and context to make an effective choice."
            ),
            "temperature": 0.35
        }
    return None