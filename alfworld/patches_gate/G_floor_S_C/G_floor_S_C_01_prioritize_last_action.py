def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    
    def extract_action_with_priority(text: str) -> str:
        # Attempt to find the last action mentioned within <action> tags
        actions = re.findall(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        for action in reversed(actions):
            action = action.strip().lower()
            if action in admissible:
                return action
                
        # If no valid action is found within tags, search the response for any admissible actions
        for action in admissible:
            if action in text.lower():
                return action
        
        # Default action if none are found
        return "look"

    # Extract and return the action, prioritizing the last valid one found
    return extract_action_with_priority(response)