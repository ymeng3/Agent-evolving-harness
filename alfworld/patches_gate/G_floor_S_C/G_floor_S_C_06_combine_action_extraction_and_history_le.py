import re

HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Extract a valid action from the model's response or fallback to default if necessary
    def extract_action(text: str) -> str:
        # Look for action inside <action> tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # Cross-verify model's responses with admissible actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action

        # Default fallback action
        return "look"

    return extract_action(response)