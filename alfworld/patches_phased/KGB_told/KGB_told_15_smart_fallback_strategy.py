HISTORY_LENGTH = 10

import random

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None


def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize actions that seem more plausible for progression, e.g., 'open', 'pick up', 'move to'
    keywords_priority = ["open", "pick up", "move to", "close", "put", "use", "turn on", "turn off"]
    
    for keyword in keywords_priority:
        for action in admissible:
            if keyword in action:
                return action
    
    # If no priority actions are found, return a random choice from admissible actions
    return random.choice(admissible)