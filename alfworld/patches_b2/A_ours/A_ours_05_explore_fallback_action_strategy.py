def choose_fallback(admissible: list[str], state: dict) -> str:
    # Heuristic to prioritize 'look' and certain verbs if available
    prioritized_verbs = ['look', 'go to', 'open', 'examine', 'check']

    # Filter admissible actions that start with prioritized verbs
    prioritized_actions = [action for action in admissible if any(action.startswith(verb) for verb in prioritized_verbs)]

    # Return first matching prioritized action
    if prioritized_actions:
        return prioritized_actions[0]

    # Default to 'look' if no specific prioritized action found
    if 'look' in admissible:
        return 'look'

    # Fall back to any admissible action if 'look' is not available
    return admissible[0]