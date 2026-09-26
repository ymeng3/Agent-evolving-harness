HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'recent_actions' not in state:
        state['recent_actions'] = []
    state['recent_actions'].append(action)
    if len(state['recent_actions']) > 5:
        state['recent_actions'].pop(0)
