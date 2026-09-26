HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {'extra_instruction': 'Make sure the action is correctly chosen from the provided list of admissible actions.'}
    if attempt == 2:
        return {'extra_instruction': 'Review your reasoning to ensure it aligns with the current state of the environment.', 'temperature': 0.3}
    return None
