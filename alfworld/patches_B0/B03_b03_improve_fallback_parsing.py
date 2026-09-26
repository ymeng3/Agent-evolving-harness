TEMPERATURE = 0.3

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            return action
    
    # Fallback: Attempt intelligent picking from visible actions
    visible_admissible = [action for action in admissible if "visible" in action]
    if visible_admissible:
        return visible_admissible[0]

    # Default fallback handling
    return admissible[0]

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Selecting an admissible action that is related to changing view or exploration
    look_actions = [action for action in admissible if "look" in action or "examine" in action]
    if look_actions:
        return look_actions[0]
    
    # Default to the first admissible action if no 'look' or 'examine' is available
    return admissible[0]