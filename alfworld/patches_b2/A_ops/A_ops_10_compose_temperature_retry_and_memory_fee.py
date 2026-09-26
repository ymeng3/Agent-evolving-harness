HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_repetitions' not in state:
        state['action_repetitions'] = collections.Counter()
    state['action_repetitions'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Ensure your action is one from the admissible list."
    
    if attempt == 1:
        extra_instruction += " Avoid picking frequently repeated actions."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    
    elif attempt == 2:
        extra_instruction += " Select an action that you haven't chosen multiple times before."
        
        # Filter out actions that have been repeated 3 or more times
        valid_admissible = [a for a in admissible if state['action_repetitions'][a] < 3]
        
        if valid_admissible:
            return {"extra_instruction": extra_instruction, "temperature": 0.4}

    return None