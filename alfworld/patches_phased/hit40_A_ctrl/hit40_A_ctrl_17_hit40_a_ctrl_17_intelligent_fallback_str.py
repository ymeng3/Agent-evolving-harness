HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Intelligent fallback strategy: Prioritize 'look' if available, otherwise choose an admissible action
    priority_action = 'look'
    if priority_action in admissible:
        return priority_action
    return admissible[0] if admissible else 'look'