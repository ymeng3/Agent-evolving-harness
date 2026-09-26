def choose_fallback(admissible: list[str], state: dict) -> str:
    # New strategy for selecting fallback action by selecting the most plausible action.
    action_priorities = ["look", "scan", "examine", "search"]
    for action in action_priorities:
        if action in admissible:
            return action
    return admissible[0]  # Default to the first admissible action if none from the priorities list are found.