def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Introduce a mechanism to intelligently choose a fallback action when all other actions fail.
    If available, prefer actions that are 'look' or 'examine' as a safe failover strategy;
    otherwise, pick the first admissible action for minimal intervention.
    """
    # Prioritize 'look' or 'examine' as a safe exploratory fallback action
    preferred_fallbacks = ['look', 'examine']
    for fallback in preferred_fallbacks:
        if fallback in admissible:
            return fallback
    
    # Default to the first admissible action if no preferred fallback is available
    return admissible[0] if admissible else 'look'