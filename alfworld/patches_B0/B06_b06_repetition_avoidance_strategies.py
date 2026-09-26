HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of the last few actions to avoid repetition.
    state.setdefault('last_actions', []).append(action)
    if len(state['last_actions']) > HISTORY_LENGTH:
        state['last_actions'].pop(0)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Retry if an action is repeated, adjusting temperature slightly to encourage variety.
    if attempt == 1 and state.get('last_actions'):
        if state['last_actions'].count(action) > 1:
            return {"extra_instruction": "Avoid repeating previous actions unless necessary.", "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # As a fallback strategy, avoid choosing recently repeated actions.
    recent_actions = set(state.get('last_actions', []))
    available_actions = [act for act in admissible if act not in recent_actions]
    return available_actions[0] if available_actions else 'look'