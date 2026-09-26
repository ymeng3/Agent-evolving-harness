HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Define a helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Search for the first action enclosed in <action> tags with a flexible pattern
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
    if attempt == 1:
        extra_instruction = (
            "Your previous action was not admissible. "
            "Ensure your selected action is one of the admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Once again, choose from the list of admissible actions. "
            "Focus on matching your action with the environment context carefully."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None