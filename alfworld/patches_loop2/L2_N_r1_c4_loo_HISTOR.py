def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        return {"extra_instruction": extra_instruction}
    return None

import random

def choose_fallback(admissible: list[str], state: dict) -> str:
    move_actions = [action for action in admissible if action.startswith('move')]
    if move_actions:
        return random.choice(move_actions)
    return random.choice(admissible)
