HISTORY_LENGTH = 10

def choose_fallback(admissible: list[str], state: dict) -> str:
    """E1: never 'look'; prefer navigation to a place not yet visited (tracked in state), else any admissible non-look action."""
    visited = state.get('_visited', [])
    for a in admissible:
        if a.startswith('go to ') and a not in visited:
            return a
    for a in admissible:
        if a != 'look' and not a.startswith('go to '):
            return a
    return admissible[0]

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
    if action.startswith('go to '):
        state.setdefault('_visited', []).append(action)
