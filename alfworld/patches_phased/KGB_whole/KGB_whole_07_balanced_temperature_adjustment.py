HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Please verify and select one of the listed admissible actions.", "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": "Carefully reconsider your choice. Only select from the admissible actions provided.", "temperature": 0.7}
    return None

import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Define a helper function to clean and refine the extracted action
    extract_action = lambda text: (
        next((action for action in admissible if action in text.lower()), "look")
    )

    action_match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    extracted_action = (action_match.group(1).strip().lower() if action_match else None)
    return extracted_action if extracted_action in admissible else extract_action(response)