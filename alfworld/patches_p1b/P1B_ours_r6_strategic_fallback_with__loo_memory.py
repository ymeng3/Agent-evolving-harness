HISTORY_LENGTH = 10

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a strategic fallback action based on the recent history of actions.
    Default to 'look' if no strategic action is found.
    """
    if 'action_history' in state and state['action_history']:
        last_action = state['action_history'][-1]
        if 'look' in admissible and last_action != 'look':
            return 'look'
        for action in reversed(state['action_history']):
            if action in admissible and action != last_action:
                return action
    return 'look' if 'look' in admissible else admissible[0]

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {'extra_instruction': 'Re-evaluate the recent steps and choose a valid action from the list provided.', 'temperature': 0.5}
    return None
