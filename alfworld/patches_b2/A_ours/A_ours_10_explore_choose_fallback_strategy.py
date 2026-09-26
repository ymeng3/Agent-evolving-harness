def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Implement a strategy to choose the fallback action when no valid action is found.
    Prioritize actions that involve observing the environment, as these may provide
    new information leading to better decision-making.
    """
    # Observing actions usually start with verbs like 'look', 'examine', 'observe'
    observe_actions = [action for action in admissible if action.startswith('look') or action.startswith('examine') or action.startswith('observe')]

    if observe_actions:
        return observe_actions[0]

    # If no observing actions are available, return the general default fallback
    # to explore more of the environment.
    return 'explore'