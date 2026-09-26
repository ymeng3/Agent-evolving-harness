HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action was invalid. Please carefully choose one of the following admissible actions."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Maintain a simple loop detection mechanism
    if 'visited_observations' not in state:
        state['visited_observations'] = set()
    
    current_state = (observation, action)
    state['visited_observations'].add(current_state)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Default fallback to the first admissible action
    return admissible[0] if admissible else 'look'