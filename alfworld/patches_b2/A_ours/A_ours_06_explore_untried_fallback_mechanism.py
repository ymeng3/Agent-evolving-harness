def choose_fallback(admissible: list[str], state: dict) -> str:
    # Selects a fallback action that isn't typically 'look', aiming for tasks that need specific interaction first.
    # If we have any 'go' actions in the admissible list, prefer them as it implies movement towards task objectives.
    for fallback_action in ['go', 'open', 'put', 'take']:
        for action in admissible:
            if action.startswith(fallback_action):
                return action
    # If none match specific fallback criteria, return the first admissible action.
    return admissible[0] if admissible else 'look'