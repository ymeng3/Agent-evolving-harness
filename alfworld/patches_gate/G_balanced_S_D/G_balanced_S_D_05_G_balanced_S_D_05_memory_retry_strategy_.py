HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Parse the action from response considering the allowed format
    import re
    match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your previous action was invalid. Consider admissible actions only."
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        instruction = "Focus on selecting an admissible action and vary from previous attempts."
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            instruction += " Avoid repeating the same action."
        return {"extra_instruction": instruction, "temperature": 0.35}
    return None