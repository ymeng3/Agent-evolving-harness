HISTORY_LENGTH = 10

def choose_fallback(admissible: list[str], state: dict) -> str:
    """V2 history-alternative only: never substitutes 'look'; repeats an earlier admissible action if any, else admissible[0]."""
    if 'action_history' in state and state['action_history']:
        last_action = state['action_history'][-1]
        for action in reversed(state['action_history']):
            if action in admissible and action != last_action and action != 'look':
                return action
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
