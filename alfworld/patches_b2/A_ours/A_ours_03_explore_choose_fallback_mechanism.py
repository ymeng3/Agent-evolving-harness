def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' action as it can give new information, aiding decision-making
    if 'look' in admissible:
        return 'look'
    
    # Pick a random action from admissible if 'look' is not an option
    import random
    return random.choice(admissible)