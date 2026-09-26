HISTORY_LENGTH = 8
TEMPERATURE = 0.5

import re

def format_prompt(prompt: str, state: dict) -> str:
    if 'last_invalid_action' in state:
        prompt += "\nNote: Your last choice was not valid, please ensure to pick from the provided admissible actions."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Focus on one of the admissible actions listed to proceed."}
    elif attempt == 2:
        return {"extra_instruction": "Ensure your action is among the admissible actions given.", "temperature": 0.6}
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
        
        state['last_invalid_action'] = True
        return "look"

    return extract_action(response)

def choose_fallback(admissible: list[str], state: dict) -> str:
    state.pop('last_invalid_action', None)
    return admissible[random.randint(0, len(admissible) - 1)]