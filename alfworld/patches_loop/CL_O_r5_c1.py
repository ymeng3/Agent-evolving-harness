def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the 'look' action if available to gather more information.
    # Otherwise, revert to the first admissible action.
    return 'look' if 'look' in admissible else admissible[0]
