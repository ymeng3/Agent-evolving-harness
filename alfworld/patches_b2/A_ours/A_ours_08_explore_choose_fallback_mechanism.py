HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' for exploration and use admissible actions to avoid cycles
    prioritized_actions = [action for action in admissible if "look" in action]
    if prioritized_actions:
        return prioritized_actions[0]
    # Default to the first admissible action, ensuring a valid choice
    return admissible[0]