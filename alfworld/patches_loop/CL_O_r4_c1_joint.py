HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    if 'task_summary' not in state:
        task_description_start = prompt.find('Your task is to:')
        task_description_end = prompt.find('Prior to this step')
        task_description = prompt[task_description_start:task_description_end].strip()
        state['task_summary'] = task_description
    step_summary = f" Task Progress: {state.get('progress', 'Task is ongoing.')}. "
    return prompt.replace("Now it's your turn to take an action.", step_summary + "Now it's your turn to take an action.")

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    last_actions = state.get('last_actions', [])
    if len(last_actions) >= 3 and all((a == last_actions[-1] for a in last_actions[-3:])):
        state['progress'] = 'Potential action repetition detected; consider alternative actions.'
    else:
        state['progress'] = 'Task is ongoing.'
