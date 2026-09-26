def choose_fallback(admissible: list[str], state: dict) -> str:
    # This fallback strategy prioritizes 'look' and 'open' actions if present in admissible actions
    fallback_priorities = ['look', 'open']
    for action in fallback_priorities:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action
    # If none of the prioritized actions are available, return the first admissible action
    return admissible[0]