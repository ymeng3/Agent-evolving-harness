HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = f"Action '{action}' was not valid. Use the list of admissible actions to guide your selection."
        return {"extra_instruction": extra_instruction, "temperature": 0.4 if attempt == 1 else 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_action'] = action  # Store the last action to help in avoiding repeated actions
    if 'tried_actions' not in state:
        state['tried_actions'] = set()
    state['tried_actions'].add(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    tried_actions = state.get('tried_actions', set())
    for action in admissible:
        if action not in tried_actions:
            return action
    return admissible[0]