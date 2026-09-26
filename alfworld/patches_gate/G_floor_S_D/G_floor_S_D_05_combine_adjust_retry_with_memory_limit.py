HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store the count of each action taken to limit excessive repetition
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Combine strategies: adjust temperature and instruct on invalid attempts, limit action repetition
    instruction = "The previous action was invalid. Focus on the admissible actions."
    
    if attempt == 1:
        temperature = 0.3
    elif attempt == 2:
        temperature = 0.25
    else:
        return None

    if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
        admissible = [a for a in admissible if a != action]
        instruction += " Avoid repeating actions excessively."

    if admissible:
        instruction += f" Choose an action different from: {action}."
    
    return {"extra_instruction": instruction, "temperature": temperature}