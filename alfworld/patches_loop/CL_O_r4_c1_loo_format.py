HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    action_start = response.find('<action>') + len('<action>')
    action_end = response.find('</action>')
    action = response[action_start:action_end].strip().lower()
    if action in admissible:
        if 'last_actions' not in state:
            state['last_actions'] = []
        state['last_actions'].append(action)
        return action
    return 'look'

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    last_actions = state.get('last_actions', [])
    if len(last_actions) >= 3 and all((a == last_actions[-1] for a in last_actions[-3:])):
        state['progress'] = 'Potential action repetition detected; consider alternative actions.'
    else:
        state['progress'] = 'Task is ongoing.'
