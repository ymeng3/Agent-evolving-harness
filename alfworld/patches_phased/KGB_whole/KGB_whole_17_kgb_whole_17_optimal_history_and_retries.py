HISTORY_LENGTH = 7
TEMPERATURE = 0.3

import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags with a more forgiving pattern
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # If no valid match is found within tags, attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        
        # Default return if none match
        return "look"

    # Extract and return the refined action
    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please select your action from the list of admissible actions based on the current situation."
    instructions_by_attempt = [
        "Your selected action was invalid. Pay attention and choose correctly.",
        "The action you chose still isn't admissible. Refer to the admissible actions."
    ]
    
    if 1 <= attempt <= len(instructions_by_attempt):
        return {"extra_instruction": instructions_by_attempt[attempt - 1]}
    return None