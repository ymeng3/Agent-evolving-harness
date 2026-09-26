import re

TEMPERATURE = 0.5

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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Ensure you choose an action from the admissible list."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.7}
    return None