HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'history' not in state:
        state['history'] = []
    state['history'].append((observation, action))
    if len(state['history']) > HISTORY_LENGTH:
        state['history'].pop(0)
