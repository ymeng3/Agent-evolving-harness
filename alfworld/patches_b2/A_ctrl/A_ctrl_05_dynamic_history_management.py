HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'actions' not in state:
        state['actions'] = []
    state['actions'].append(action)
    
    # Determine dynamic history length based on observed effect of last action
    if "successfully" in next_observation:
        state['recent_success'] = True
    elif "cannot" in next_observation or "unsuccessfully" in next_observation:
        state['recent_success'] = False

def format_prompt(prompt: str, state: dict) -> str:
    # Adjust the history length based on past success or failure trends
    if state.get('recent_success', True):
        effective_history_length = min(len(state['actions']), 3)  # Short history if recent success
    else:
        effective_history_length = min(len(state['actions']), 7)  # Longer history if recent failure
    
    # Format the recent history into the prompt
    action_history_snippet = state['actions'][-effective_history_length:]
    action_history_formatted = '; '.join(action_history_snippet)
    prompt = prompt.replace("{action_history}", action_history_formatted)
    
    return prompt