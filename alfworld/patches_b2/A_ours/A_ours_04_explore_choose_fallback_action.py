def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Selects a fallback action when all else fails. Prioritizes exploration actions to
    minimize the frequency of encountering dead-ends.
    """
    # Prefer actions that are exploratory, minimizing chances of loops
    exploration_priorities = ["look", "move", "open", "close", "push", "pull"]
    
    # Pick an action from exploration_priorities if it is admissible
    for action in exploration_priorities:
        if action in admissible:
            return action
    
    # If no preferred exploratory action is admissible, return the first admissible action
    return admissible[0] if admissible else "look"