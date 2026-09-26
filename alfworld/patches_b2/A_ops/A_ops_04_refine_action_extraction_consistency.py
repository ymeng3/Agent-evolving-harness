import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    """Refine action extraction to address different possible areas in positioning"""
  
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags and consider possible positional variations
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # Check for multiple <action> tags and prefer when an admissible action is nested
        action_matches = re.findall(r"<action>(.*?)</action>", text, re.IGNORECASE)
        for potential in action_matches:
            potential_action = potential.strip().lower()
            if potential_action in admissible:
                return potential_action

        # Fallback: attempt to match actions directly from the text (ignoring redundancy)
        text_lower = text.lower()
        seen_actions = set()
        for action in admissible:
            if action in text_lower and action not in seen_actions:
                seen_actions.add(action)
                if len(seen_actions) == 1: # The first match of unique admissible action
                    return action
        
        # Default return if none match
        return "look"

    # Extract and return the refined action
    return extract_action(response)