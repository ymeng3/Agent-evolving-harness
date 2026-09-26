HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Store prompt in state for use in retry logic
    state['last_prompt'] = prompt
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Consider the admissible actions carefully."
    # Retry with adjusted temperature based on attempts
    if attempt == 1:
        state['attempted_actions'] = state.get('attempted_actions', []) + [action]
        return {"extra_instruction": extra_instruction + " Attempt once.", "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction + " Attempt twice.", "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Return the first admissible action that hasn't been attempted yet
    for action in admissible:
        if action not in state.get('attempted_actions', []):
            return action
    return 'look'  # Default fallback action