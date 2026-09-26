def choose_fallback(admissible: list[str], state: dict) -> str:
    return "look around" if "look around" in admissible else admissible[0]
