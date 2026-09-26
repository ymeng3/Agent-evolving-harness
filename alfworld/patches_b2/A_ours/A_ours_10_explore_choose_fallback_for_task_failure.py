def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize actions related to common unresolved task categories
    task_priorities = [
        "pick up",    # Common action for pick tasks
        "place",      # Common action for place tasks
        "look"        # Default observation action to minimize penalties
    ]
    
    # Attempt to choose a fallback based on task prioritization
    for action in task_priorities:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action
    
    # If no prioritized action is found, default to the first admissible action
    return admissible[0] if admissible else "look"