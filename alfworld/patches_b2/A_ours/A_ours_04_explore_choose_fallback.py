def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Instead of defaulting to 'look', this function intelligently selects an admissible action 
    based on past actions and the admissible list, aiming to diversify actions when stuck.
    """
    # Initialize the state for tracking fallback use count if it doesn't exist
    if 'fallback_use_count' not in state:
        state['fallback_use_count'] = 0

    # Track how many times fallback was invoked
    state['fallback_use_count'] += 1

    # Consider choosing an admissible action different from the most recent actions
    if state.get('action_history'):
        last_action = state['action_history'][-1]
        diversified_choices = [a for a in admissible if a != last_action]
        if diversified_choices:
            return diversified_choices[0]  # Return the first from diversified options

    # If it repeatedly uses fallback, default to a random admissible action
    if state['fallback_use_count'] > 2:
        import random
        return random.choice(admissible)

    # Default fallback action if none of the above conditions met
    return 'look'

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the action history in the state
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)