def choose_fallback(admissible: list[str], state: dict) -> str:
    # Given the admissible actions, choose a plausible default action other than 'look'
    fallback_candidates = ["move", "push", "pull", "pick", "open", "close"]
    for action in fallback_candidates:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action
    # If no strategic action found, default to 'look'
    return "look"
