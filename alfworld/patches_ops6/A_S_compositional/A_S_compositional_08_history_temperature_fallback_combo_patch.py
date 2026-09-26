HISTORY_LENGTH = 10
TEMPERATURE = 0.35

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer a 'look' action as a fallback if it is admissible
    look_actions = [action for action in admissible if 'look' in action]
    if look_actions:
        return look_actions[0]
    # Otherwise, just fallback to the first admissible action
    return admissible[0]