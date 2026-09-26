HISTORY_LENGTH = 10

import re


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Remember to choose an action that directly affects the current object of interest."
    if attempt == 1 or attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None


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
        admissible_set = set(admissible)  # Use a set for faster checks
        response_lower = text.lower()
        
        # Consider longest admissible matches first for ambiguity reduction
        sorted_admissible = sorted(admissible, key=len, reverse=True)
        
        for action in sorted_admissible:
            if action in response_lower:
                return action
        
        # Default return if none match
        return "look"

    # Extract and return the refined action
    return extract_action(response)