def choose_fallback(admissible: list[str], state: dict) -> str:
    # Implement a simple strategy to choose the fallback action
    # Prefer exploration actions as a potential default fallback: check inventory or look around
    potential_actions = ["check inventory", "look"]
    for action in potential_actions:
        if action in admissible:
            return action
    
    # If none of the preferred exploration actions are available, default to the first admissible action
    return admissible[0]