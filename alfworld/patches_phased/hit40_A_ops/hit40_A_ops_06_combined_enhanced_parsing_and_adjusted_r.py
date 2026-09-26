import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Improved action extraction strategy
    def extract_action(text: str) -> str:
        # First attempt to extract text within <action> tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
      
        # Fallback to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        
        # Default to 'look' if no valid action is found
        return "look"

    # Use improved logic to extract and return the action
    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Your previous action was not in the admissible list. Carefully consider the current environment and choose from the provided actions.",
            "temperature": 0.5  # Adjust temperature for more creative responses
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Please ensure your action selection is from the admissible list, and try to understand the environmental context.",
            "temperature": 0.3  # Lower temperature for consistency
        }
    return None