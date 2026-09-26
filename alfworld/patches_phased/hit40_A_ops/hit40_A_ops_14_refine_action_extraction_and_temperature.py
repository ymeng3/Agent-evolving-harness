import re

TEMPERATURE = 0.5

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # A refined action extraction technique
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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"temperature": 0.3}  # Introduce cooler temperature on first retry
    elif attempt == 2:
        return {"temperature": 0.2}  # Further reduction on second retry
    return None