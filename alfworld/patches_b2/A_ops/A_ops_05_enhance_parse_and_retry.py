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
    extra_instruction = "Remember to focus on the admissible actions listed."
    if attempt == 1:
        # On the first retry, remind to focus on admissible actions and adjust temperature
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.35
        }
    elif attempt == 2:
        # On the second retry, further emphasize choosing from the admissible list and set temperature for more determinism
        return {
            "extra_instruction": "It's critical to select from admissible actions now.",
            "temperature": 0.3
        }
    return None