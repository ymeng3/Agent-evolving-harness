import re

HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Helper function to clean and refine the extracted action
    def extract_action(text: str) -> str:
        # Look for actions within <action> tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action

        # Look for direct matches if no valid action is found in tags
        for action in admissible:
            if action in text.lower():
                return action

        # Default to 'look' if no valid action is found
        return "look"

    # Extract and return the refined action
    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        # Add extra instruction emphasizing the action selection process
        extra_instruction = (
            "Your previous action was not admissible. Focus on selecting an action "
            "that is explicitly listed in the admissible actions and fits the current context."
        )
        return {"extra_instruction": extra_instruction}
    return None