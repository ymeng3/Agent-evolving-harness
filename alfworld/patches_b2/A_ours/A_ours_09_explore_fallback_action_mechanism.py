def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    A fallback strategy that selects one of the less frequently used actions from admissible actions
    based on the cumulative action count stored in the state.
    """
    action_counts = state.get('action_counts', {})
    
    # Default fallback action if no counts are available
    fallback_action = 'look'
    
    # Select the admissible action with the least usage count
    min_count = float('inf')
    for action in admissible:
        count = action_counts.get(action, 0)
        if count < min_count:
            min_count = count
            fallback_action = action
    
    return fallback_action

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Updates cumulative action count in the state after each step.
    """
    if 'action_counts' not in state:
        state['action_counts'] = {}
    if action not in state['action_counts']:
        state['action_counts'][action] = 0
    state['action_counts'][action] += 1