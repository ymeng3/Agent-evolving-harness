HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'history' not in state:
        state['history'] = []
    state['history'].append((observation, action))
    if len(state['history']) > HISTORY_LENGTH:
        state['history'].pop(0)
