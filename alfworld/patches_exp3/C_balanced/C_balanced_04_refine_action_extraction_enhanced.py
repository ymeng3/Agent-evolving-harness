import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Try extracting the action from tags with enhanced pattern forgiving spaces and capitalization
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action

        # Check if any admissible action appears verbatim in the response, starting from most likely actions
        likely_actions = sorted(admissible, key=lambda a: text.lower().count(a), reverse=True)
        for action in likely_actions:
            if action in text.lower():
                return action

        # Default to a safe fallback if no matches are found
        return "look"

    # Extract and return the refined action
    return extract_action(response)