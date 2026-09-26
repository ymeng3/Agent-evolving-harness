import re

HISTORY_LENGTH = 10
TEMPERATURE = 0.35

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action

        # Attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"

    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": (
                "Ensure your action is drawn from the admissible actions. "
                "Think about the current environment state before choosing."
            ),
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": (
                "Choose carefully from the admissible actions this time. "
                "Reassess the scene and make a clear decision."
            ),
            "temperature": 0.25
        }
    return None