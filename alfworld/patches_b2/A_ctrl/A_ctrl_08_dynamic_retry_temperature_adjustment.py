def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Make the retry strategy adjust temperature based on previous action validity
    if 'previous_invalid' not in state:
        state['previous_invalid'] = 0

    if attempt < 2:
        # Increase temperature slightly if the previous action was invalid
        if state['previous_invalid']:
            new_temperature = 0.5
        else:
            new_temperature = 0.4
        
        # Update state for whether the current action is invalid
        state['previous_invalid'] = 0 if action in admissible else 1

        return {"temperature": new_temperature}

    return None