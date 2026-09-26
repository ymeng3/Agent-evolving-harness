def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # On the first retry, provide explicit feedback and slightly lower the temperature.
        return {
            "extra_instruction": (
                "Your previous action was not admissible. Please choose an action from the list of admissible actions."
            ),
            "temperature": 0.3
        }
    elif attempt == 2:
        # Further lower the temperature on the second retry and emphasize admissible actions.
        return {
            "extra_instruction": (
                "Make sure to focus on the admissible actions provided. Selecting an action from the list is crucial."
            ),
            "temperature": 0.25
        }
    return None