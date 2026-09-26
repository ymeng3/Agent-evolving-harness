def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer 'look' if present, as it's typically a safe exploratory action.
    if 'look' in admissible:
        return 'look'
    # If 'look' is not available, return the first admissible action.
    return admissible[0] if admissible else 'look'