HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action was not valid. Ensure you choose one from the provided admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": "Focus on the task requirements and select a valid action.", "temperature": 0.6}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Use a simple heuristic: prioritize actions based on typical task needs
    prioritized_actions = ['look', 'pick', 'put', 'open', 'close']
    for action in prioritized_actions:
        matching_actions = [a for a in admissible if action in a]
        if matching_actions:
            return matching_actions[0]
    return admissible[0]