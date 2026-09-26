HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action wasn't valid. Ensure to select one of the admissible actions listed."
        " Pay special attention to the context and the task goal."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    return None

import re

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
    important_actions = ['look', 'inspect']
    for action in important_actions:
        if action in admissible:
            return action
    return admissible[0] if admissible else 'look'