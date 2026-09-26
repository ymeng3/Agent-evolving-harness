import re

HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Helper function for robust action extraction
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        # Attempt to match actions directly from the response text
        for action in admissible:
            if action in text.lower():
                return action
        # Default action if none match
        return "look"

    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Review your reasoning steps carefully."
        )
        return {"extra_instruction": extra_instruction}
    return None