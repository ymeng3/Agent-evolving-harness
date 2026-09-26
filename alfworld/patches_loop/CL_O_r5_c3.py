import collections

HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = collections.deque(maxlen=3)
    state['action_history'].append(action)

    repeated_actions = len(set(state['action_history'])) == 1
    if repeated_actions:
        global HISTORY_LENGTH
        HISTORY_LENGTH = 3

# Other hooks are not defined, meaning the default behaviour will be used for them.
