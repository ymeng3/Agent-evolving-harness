def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a strategic fallback action based on the recent history of actions.
    Default to 'look' if no strategic action is found.
    """
    if 'action_history' in state and state['action_history']:
        last_action = state['action_history'][-1]

        # If the last action wasn't 'look', prioritize 'look'
        if 'look' in admissible and last_action != 'look':
            return 'look'

        # Attempt to find an alternative admissible action from history
        for action in reversed(state['action_history']):
            if action in admissible and action != last_action:
                return action

    return 'look' if 'look' in admissible else admissible[0]

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {
            "extra_instruction": "Re-evaluate the recent steps and choose a valid action from the list provided.",
            "temperature": 0.5
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)
