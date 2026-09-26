HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Creating a prioritized fallback strategy based on common actions
    common_actions = {'look', 'examine', 'search', 'inspect'}
    prioritized_actions = [action for action in common_actions if action in admissible]
    
    # Choose the most prioritized action or default to the first admissible action
    return prioritized_actions[0] if prioritized_actions else admissible[0]