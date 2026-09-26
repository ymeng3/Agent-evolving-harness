import random

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to choose a non-repetitive action as fallback
    move_actions = [action for action in admissible if action.startswith('move')]
    if move_actions:
        return random.choice(move_actions)
    return random.choice(admissible)
