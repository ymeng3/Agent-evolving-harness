HISTORY_LENGTH = 10
TEMPERATURE = 0.4

import re

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Consider re-evaluating your choice based on these admissible actions."
    confidence_threshold = state.get('confidence_threshold', 0.8)
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - 0.1}
    elif attempt == 2:
        return {"extra_instruction": f"{extra_instruction} Remember, selecting an admissible action is crucial.", "temperature": TEMPERATURE + 0.1}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                state['confidence'] = 1.0
                return action
        
        for action in admissible:
            if action in text.lower():
                state['confidence'] = 0.9
                return action
        
        state['confidence'] = 0
        return "look"

    action = extract_action(response)
    state['confidence_threshold'] = 0.8 if state.get('confidence', 0) >= 0.5 else 0.7
    return action