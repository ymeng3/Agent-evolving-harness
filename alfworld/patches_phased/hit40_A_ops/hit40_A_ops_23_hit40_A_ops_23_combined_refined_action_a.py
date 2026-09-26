import re

HISTORY_LENGTH = 10

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
    if 'action_count' not in state:
        state['action_count'] = {}
    state['action_count'][action] = state['action_count'].get(action, 0) + 1
    
    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        if state.get('action_count', {}).get(action, 0) >= 3:
            admissible = [a for a in admissible if a != action]
            extra_instruction = f"Your last action was invalid. Avoid repeating '{action}' excessively. Choose an action different from your previous choices."
        else:
            extra_instruction = "Your last action was invalid. Focus on the provided admissible actions."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_states' not in state:
        state['visited_states'] = set()
    state['visited_states'].add(observation)