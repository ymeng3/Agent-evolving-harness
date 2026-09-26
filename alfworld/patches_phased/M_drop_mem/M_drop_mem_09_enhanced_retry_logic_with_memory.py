HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    state.setdefault('retry_count', 0)
    
    extra_instruction = "Your last action wasn't valid. Carefully analyze the admissible actions and choose one."
    
    # Extra instruction improves focus, increased temperature adds variability
    if attempt == 1:
        state['retry_count'] += 1
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        state['retry_count'] += 1
        # Reset temperature, no extra instruction needed, strictly choose an action
        return {"extra_instruction": "You must select an admissible action now."}
    
    state['retry_count'] = 0
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track recent actions to potentially detect loops or repetitive failures
    action_history = state.setdefault('action_history', [])
    action_history.append(action)
    if len(action_history) > 50:
        action_history.pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    if 'retry_count' in state and state['retry_count'] > 2:
        # Prioritize a safe "look" action during repeated failures
        for action in admissible:
            if "look" in action:
                return action
    return admissible[0]