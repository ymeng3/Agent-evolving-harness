HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'previous_actions' not in state:
        state['previous_actions'] = []
    
    # Store the last 5 actions to help detect loops and repetitive behavior
    state['previous_actions'].append(action)
    if len(state['previous_actions']) > 5:
        state['previous_actions'].pop(0)