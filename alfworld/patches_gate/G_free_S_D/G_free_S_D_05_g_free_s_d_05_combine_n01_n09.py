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
    """
    Modifies the retry strategy to add extra instructions to the prompt when the model suggests an invalid action.
    """
    if attempt == 1:
        # If the first attempt failed, provide a hint to focus on the admissible actions.
        return {
            "extra_instruction": "Focus on the admissible actions provided and choose from them.",
            "temperature": 0.3  # Slightly reduce temperature to promote more deterministic responses.
        }
    elif attempt == 2:
        # If the second attempt also failed, further emphasize the need to select from admissible actions.
        return {
            "extra_instruction": "It's crucial to select an action from the admissible list now.",
            "temperature": 0.25  # Further reduce temperature for even more deterministic behavior.
        }
    return None