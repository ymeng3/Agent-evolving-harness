def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a fallback action when no admissible actions are selected.
    This implementation attempts to choose the most informative action available.
    """
    # Prioritize actions that can potentially reveal more about the environment state
    informative_actions = ['look', 'examine', 'scan', 'check']

    # Try to find an informative action within the admissible actions
    for action in informative_actions:
        if action in admissible:
            return action

    # Default to the first admissible action if none of the informative actions are available
    return admissible[0] if admissible else 'look'