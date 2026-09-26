HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Consider the history of actions and observations to choose an admissible action."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = "Reflect again on recent steps to select an action from the admissible list."
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'history' not in state:
        state['history'] = []
    state['history'].append((observation, action))
    if len(state['history']) > HISTORY_LENGTH:
        state['history'].pop(0)
