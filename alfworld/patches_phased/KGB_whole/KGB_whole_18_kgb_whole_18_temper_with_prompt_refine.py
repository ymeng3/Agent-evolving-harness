HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please ensure that the action you choose is one of the admissible actions provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.7}
    return None


import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to refine the action extraction process
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