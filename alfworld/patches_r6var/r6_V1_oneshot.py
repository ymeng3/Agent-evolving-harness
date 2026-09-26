HISTORY_LENGTH = 10

def choose_fallback(admissible: list[str], state: dict) -> str:
    """V1 one-shot: identical to r6's fallback the first time it fires in an episode; afterwards returns the raw action path (no substitution)."""
    if state.get('_fb_fired'):
        return ''   # not admissible -> harness keeps the model's action (fallback effectively off)
    state['_fb_fired'] = True
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
        return {
            "extra_instruction": "Re-evaluate the recent steps and choose a valid action from the list provided.",
            "temperature": 0.5
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)
