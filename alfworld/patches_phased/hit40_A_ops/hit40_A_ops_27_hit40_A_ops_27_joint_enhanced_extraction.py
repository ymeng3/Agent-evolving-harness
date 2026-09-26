TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    
    # Enhanced action extraction mechanism to increase admissible choices
    def extract_action_enhanced(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # If initial extract doesn't work, try direct scanning for admissible actions
        for possible_action in admissible:
            if possible_action in text.lower():
                return possible_action
        
        # Fallback to a default admissible action
        return "look"
    
    return extract_action_enhanced(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Combines retry strategy with enhanced action extraction by modifying temperature and adjusting feedback.
    """
    if attempt == 1:
        # Provide a hint and adjust temperature moderately
        return {
            "extra_instruction": "Remember to strictly select an action from the given admissible options.",
            "temperature": 0.3
        }
    elif attempt == 2:
        # Further emphasize caution and lower temperature more for determinism
        return {
            "extra_instruction": "It's crucial to select an action from the admissible options only.",
            "temperature": 0.2
        }
    return None