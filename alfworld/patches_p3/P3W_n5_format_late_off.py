HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = 'Please choose a more contextually appropriate action from the admissible list.'
        return {'extra_instruction': extra_instruction}
    elif attempt == 2:
        extra_instruction = "It's important to select one of the admissible actions carefully."
        temperature_decrease = 0.2
        return {'extra_instruction': extra_instruction, 'temperature': temperature_decrease}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    state['_n_fo'] = state.get('_n_fo', 0) + 1
    if not state['_n_fo'] <= 15:
        return prompt
    modified_prompt = 'Remember to stay focused on the task goal at each step. ' + prompt
    return modified_prompt
