HISTORY_LENGTH = 8

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'history' not in state:
        state['history'] = []
    state['history'].append(action)

    if len(state['history']) > 3:  # detect loops
        most_recent_actions = state['history'][-3:]
        if all(act == most_recent_actions[0] for act in most_recent_actions):
            state['loop_detected'] = True
        else:
            state['loop_detected'] = False