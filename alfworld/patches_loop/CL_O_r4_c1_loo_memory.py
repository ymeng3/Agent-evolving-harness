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

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    action_start = response.find('<action>') + len('<action>')
    action_end = response.find('</action>')
    action = response[action_start:action_end].strip().lower()
    if action in admissible:
        if 'last_actions' not in state:
            state['last_actions'] = []
        state['last_actions'].append(action)
        return action
    return 'look'
