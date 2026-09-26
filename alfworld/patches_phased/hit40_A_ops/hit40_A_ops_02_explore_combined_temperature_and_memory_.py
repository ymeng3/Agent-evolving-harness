HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Your previous action was not admissible. Please focus on selecting a valid action from the list of admissible actions."
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            extra_instruction += f" Avoid repeating the action: {action}."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1