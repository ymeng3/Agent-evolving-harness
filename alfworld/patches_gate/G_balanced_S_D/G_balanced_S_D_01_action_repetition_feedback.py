def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize or update the count of consecutive same actions within this function
    if 'last_action' not in state:
        state['last_action'] = None
        state['repetition_count'] = 0
        
    if action == state['last_action']:
        state['repetition_count'] += 1
    else:
        state['repetition_count'] = 1
        
    state['last_action'] = action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # This function provides feedback if the same invalid action is repeated consecutively
    if attempt < 2:
        extra_instruction = "The previous action was invalid."
        if state.get('repetition_count', 0) > 2:
            extra_instruction += " Avoid repeating the same action multiple times. Consider different alternatives."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None