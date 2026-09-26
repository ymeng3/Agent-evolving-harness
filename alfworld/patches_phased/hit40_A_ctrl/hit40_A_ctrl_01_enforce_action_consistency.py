HISTORY_LENGTH = 7
TEMPERATURE = 0.35

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Extract action within <action></action> tags
    action_match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if action_match:
        raw_action = action_match.group(1).strip().lower()
        if raw_action in admissible:
            state["last_admissible_action"] = raw_action
            return raw_action
    
    # If no valid action found within tags, default to last known good action or "look"
    return state.get("last_admissible_action", "look")