HISTORY_LENGTH = 10
TEMPERATURE = 0.5

import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags with a more forgiving pattern
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()
            # Use case-insensitive comparison to check if the action is admissible
            if any(action.lower() == adm.lower() for adm in admissible):
                return action.lower()

        # If no valid match is found within tags, attempt to match actions directly from the text
        for action in admissible:
            if action.lower() in text.lower():
                return action.lower()

        # Default return if none match
        return "look"

    # Extract and return the refined action
    return extract_action(response)


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Use a streamlined retry instruction for invalid actions
    if attempt == 1:
        return {"extra_instruction": "Refocus and choose from the admissible actions listed."}
    elif attempt == 2:
        return {"extra_instruction": "Choose a valid action from the list. Verify each option carefully."}
    return None