HISTORY_LENGTH = 7
TEMPERATURE = 0.45

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction = "Ensure the action is chosen from the admissible list."
    if attempt == 1:
        return {"extra_instruction": instruction, "temperature": 0.5}
    elif attempt == 2:
        # Emphasize avoiding previous erroneous actions
        instruction += " Avoid repeating non-admissible actions."
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_memory' not in state:
        state['action_memory'] = {}
    if action in state['action_memory']:
        state['action_memory'][action] += 1
    else:
        state['action_memory'][action] = 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer admissible actions that have been less frequently used
    if 'action_memory' in state:
        sorted_actions = sorted(admissible, key=lambda x: state['action_memory'].get(x, 0))
        return sorted_actions[0]
    return admissible[0]