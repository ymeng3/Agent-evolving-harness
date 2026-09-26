HISTORY_LENGTH = 6

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if 'successfully' in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ''

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = 'Recall the guidance on successful actions. Focus on choosing from admissible options.'
        return {'extra_instruction': extra_instruction, 'temperature': 0.5}
    elif attempt == 2:
        extra_instruction = 'Choose an action from admissible options that aligns with previous successes.'
        return {'extra_instruction': extra_instruction, 'temperature': 0.4}
    return None
