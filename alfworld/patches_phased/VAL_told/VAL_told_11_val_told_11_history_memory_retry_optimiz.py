HISTORY_LENGTH = 8

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    retry_instructions = [
        "The previous action was invalid. Concentrate on choosing from the admissible actions.",
        "Let's try that again. Make sure to select an action from the list of admissible options."
    ]
    if attempt == 1:
        return {"extra_instruction": retry_instructions[0], "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": retry_instructions[1], "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_history' not in state:
        state['action_history'] = collections.deque(maxlen=5)
    state['action_history'].append((observation, action))

    prev_actions = list(state['action_history'])
    repeated_action_check = lambda history: len(history) >= 3 and all(history[-1][1] == h[1] for h in history[-3:])
    
    if repeated_action_check(prev_actions):
        state['repeat_warning'] = True
    else:
        state.pop('repeat_warning', None)