HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'recent_actions' not in state:
        state['recent_actions'] = []
    state['recent_actions'].append(action)
    if len(state['recent_actions']) > 20:
        state['recent_actions'] = state['recent_actions'][-20:]

def format_prompt(prompt: str, state: dict) -> str:
    actions_frequency = {}
    for action in state.get('recent_actions', []):
        actions_frequency[action] = actions_frequency.get(action, 0) + 1

    sorted_actions = sorted(actions_frequency.items(), key=lambda x: x[1], reverse=True)
    frequent_actions_note = "Actions you executed most frequently in recent steps: " + ", ".join(
        [f"{action}({count})" for action, count in sorted_actions])

    return prompt + "\n" + frequent_actions_note