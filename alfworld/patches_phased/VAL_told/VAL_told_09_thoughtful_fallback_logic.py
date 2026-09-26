HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    prioritization_order = [
        "look", 
        "open", 
        "close", 
        "put", 
        "take"
    ]
    for action_prefix in prioritization_order:
        for action in admissible:
            if action.startswith(action_prefix):
                return action
    return admissible[0]