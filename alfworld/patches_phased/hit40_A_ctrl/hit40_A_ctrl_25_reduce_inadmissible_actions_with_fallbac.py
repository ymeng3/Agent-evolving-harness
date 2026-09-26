HISTORY_LENGTH = 5

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Attempt to extract the action text within the <action> tags
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action

    # Attempt to extract any matching admissible action directly from the response text
    for action in admissible:
        if action in response.lower():
            return action

    # Default to 'look' if no valid action can be parsed
    return "look"

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Enhancing the fallback selection by choosing a more meaningful action instead of default 'look'
    if 'explore' in admissible:
        return 'explore'
    elif 'move' in admissible:
        return 'move'

    return 'look'