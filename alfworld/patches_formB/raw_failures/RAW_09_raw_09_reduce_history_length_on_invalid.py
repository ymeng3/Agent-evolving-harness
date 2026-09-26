HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # On the first retry, reduce history length to focus more on the current state.
        state['retry'] = True
        return {"extra_instruction": "Please refocus on the current step and make sure to select an action from the list of admissible actions.", "temperature": 0.3}
    elif attempt == 2:
        # Maintain history reduction on subsequent retries
        return {"extra_instruction": "Ensure your action is selected from the admissible actions.", "temperature": 0.2}
    return None