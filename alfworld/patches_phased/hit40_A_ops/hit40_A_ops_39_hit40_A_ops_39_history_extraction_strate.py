HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Function to extract the best matching action
    def extract_action(text: str) -> str:
        # Search for the action within tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action

        # Fallback: look for an admissible action mentioned in the response
        for action in admissible:
            if action in text.lower():
                return action

        # Default action if none matches
        return "look"

    # Use the helper to extract the intended action from the response
    return extract_action(response)