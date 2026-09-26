HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)

def format_prompt(prompt: str, state: dict) -> str:
    if 'action_history' in state and len(state['action_history']) >= 3:
        prompt += "\nNote: Avoid repeating actions that have been taken multiple times unless necessary."
    return prompt