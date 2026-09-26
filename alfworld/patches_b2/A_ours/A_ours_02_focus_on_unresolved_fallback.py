def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' if available, as it often leads to more information about the environment.
    if 'look' in admissible:
        return 'look'
    
    # Heuristic: if 'examine' is in admissible actions, it can also provide contextual information.
    if 'examine' in admissible:
        return 'examine'
    
    # Default to the first admissible action if none of the above criteria are met.
    return admissible[0]