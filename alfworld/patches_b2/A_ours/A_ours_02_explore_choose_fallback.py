def choose_fallback(admissible: list[str], state: dict) -> str:
    """Select an action that is most likely to lead to progress."""
    # Prioritize "look" or "go" actions that can provide new information or movement
    prioritized_actions = ['look', 'go', 'examine']
    for action in prioritized_actions:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action

    # Fallback to the first admissible action if none of the priorities match
    return admissible[0]