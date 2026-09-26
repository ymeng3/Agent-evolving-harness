HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)
    if len(state['action_history']) > 3:
        state['action_history'].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the fallback action by avoiding the most recently repeated action
    if state['action_history']:
        last_action = state['action_history'][-1]
        if last_action in admissible:
            admissible.remove(last_action)
    return admissible[0] if admissible else 'look'