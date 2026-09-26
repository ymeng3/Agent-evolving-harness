import re

HISTORY_LENGTH = 7

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

    action = extract_action(response)
    if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
        admissible = [a for a in admissible if a != action]
        if admissible:
            return admissible[0]  # choose another admissible action
    return action

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    state['action_count'][action] = state['action_count'].get(action, 0) + 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        instruction = " The previous action was invalid. "
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            instruction += "Avoid repeating actions excessively. "
        if admissible:
            instruction += f"Choose an action different from: {action}."
        return {"extra_instruction": instruction, "temperature": 0.4}
    return None