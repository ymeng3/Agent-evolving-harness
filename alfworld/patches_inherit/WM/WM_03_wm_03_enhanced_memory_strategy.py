HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory if not already done
    if 'visited_objects' not in state:
        state['visited_objects'] = set()
    
    # Update visited objects based on observation
    if observation:
        # Extract the object name if it exists in the observation string
        extract_object = lambda obs: obs.split(' ')[-1] if ' ' in obs else obs
        observed_object = extract_object(observation)
        state['visited_objects'].add(observed_object)
    
def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize unvisited actions if available
    unvisited_actions = [action for action in admissible if action not in state.get('visited_objects', set())]
    return unvisited_actions[0] if unvisited_actions else admissible[0]