def choose_fallback(admissible: list[str], state: dict) -> str:
    # Always fall back to the first admissible action
    return admissible[0]
