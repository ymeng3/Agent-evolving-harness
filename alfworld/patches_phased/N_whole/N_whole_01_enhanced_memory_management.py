HISTORY_LENGTH = 15

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

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_observation'] = next_observation
    state['last_action'] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    last_action = state.get('last_action', '')
    if last_action in admissible:
        return last_action
    return 'look'