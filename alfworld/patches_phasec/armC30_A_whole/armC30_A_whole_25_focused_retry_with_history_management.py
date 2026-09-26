HISTORY_LENGTH = 8
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The previous action was invalid. Carefully choose from the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    if len(state.get('visited', [])) >= 5:
        prompt = prompt.replace("Now it's your turn to take an action.", "Consider previously visited areas and optimize your path.")
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = []
    if action not in state['visited']:
        state['visited'].append(action)
        if len(state['visited']) > 5:
            state['visited'].pop(0)