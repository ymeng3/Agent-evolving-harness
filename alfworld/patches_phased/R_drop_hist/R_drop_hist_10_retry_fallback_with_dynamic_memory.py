TEMPERATURE = 0.5
HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action was not valid. Make sure to select one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault('visited_observations', set()).add(observation)
    if 'last_action' not in state or state['last_action'] != action:
        state['last_action'] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Avoid repeating the last attempted action if it's among admissible choices
    if 'last_action' in state:
        alternatives = [a for a in admissible if a != state['last_action']]
        if alternatives:
            return alternatives[0]
    return admissible[0]