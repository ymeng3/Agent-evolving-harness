HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    elif attempt == 2:
        last_steps_memory = state.get('last_steps_memory', None)
        if last_steps_memory:
            extra_instruction += f" Note: A similar unsuccessful action sequence was detected: {last_steps_memory}. Avoid repeating it."
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append((observation, action))
    
    # Update memory of last few actions to avoid repeating unsuccessful patterns
    if len(state['action_history']) > HISTORY_LENGTH:
        state['action_history'].pop(0)
    
    # Detect a repeated action pattern that led to failure
    if len(state['action_history']) >= 3:
        actions_to_check = [act for obs, act in state['action_history'][-3:]]
        if len(set(actions_to_check)) == 1:
            state['last_steps_memory'] = " -> ".join(actions_to_check)
        else:
            state['last_steps_memory'] = None