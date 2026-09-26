def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' related actions as fallback if available, to gather more information
    for action in admissible:
        if 'look' in action:
            return action
    # If no 'look' actions, return the first admissible action
    return admissible[0]