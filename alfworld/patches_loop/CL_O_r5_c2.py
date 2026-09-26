def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a strategic fallback action based on the recent history of actions.
    If no history is available, default to 'look'.
    """
    if 'action_history' in state and state['action_history']:
        # If the last taken action wasn't 'look', prioritize 'look' as fallback
        last_action = state['action_history'][-1]
        if 'look' in admissible and last_action != 'look':
            return 'look'

        # Attempt to find a different admissible action from the most recent history step if possible
        for action in reversed(state['action_history']):
            if action in admissible and action != last_action:
                return action

    # Default to 'look' if no strategic action is found
    return 'look'

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Persist the action in the state for future fallback decision making.
    """
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)
