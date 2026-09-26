HISTORY_LENGTH = 10
import random

def choose_fallback(admissible: list[str], state: dict) -> str:
    move_actions = [action for action in admissible if action.startswith('move')]
    if move_actions:
        return random.choice(move_actions)
    return random.choice(admissible)
