HISTORY_LENGTH = 10

import re

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        for action in admissible:
            if action in text.lower():
                return action
        return "look"
    return extract_action(response)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Select the last admissible action in the list to avoid repeat earlier actions
    return admissible[-1] if admissible else "look"