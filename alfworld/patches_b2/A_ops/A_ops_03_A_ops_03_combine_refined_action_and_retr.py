import re

HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Attempt to extract a valid action from <action> tags or directly from response text
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # As fallback, try to directly match an admissible action in the response
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"

    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Provide extra instructions to focus on admissible actions and vary temperature for retries
    extra_instruction = (
        " Ensure the selected action is valid and chosen from the admissible actions provided."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None