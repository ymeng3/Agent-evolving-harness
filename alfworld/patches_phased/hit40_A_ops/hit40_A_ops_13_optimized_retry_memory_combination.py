HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        instruction = " Your last action was invalid."
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            instruction += " It seems you've repeated actions. Try something different. "
        if admissible:
            instruction += f"Choose a different action than {action}, if possible."
        return {"extra_instruction": instruction, "temperature": 0.35}
    return None