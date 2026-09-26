HISTORY_LENGTH = 10
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # First retry attempt: provide extra instruction to focus on admissible actions.
        return {"extra_instruction": "Ensure the action is one of the admissible actions listed."}
    elif attempt == 2:
        # Second retry attempt: adapt temperature to increase randomness and explore alternative actions.
        return {"temperature": 0.7}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    # Modify the prompt to remind the model of focusing on valid actions if previous invalid actions were made.
    if state.get('recent_invalid'):
        return prompt + "\n" + "Make sure to select an admissible action."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of recent invalid action attempts to adapt the prompt dynamically.
    if 'recent_invalid' not in state:
        state['recent_invalid'] = False
    if action not in next_observation.lower():
        state['recent_invalid'] = True
    else:
        state['recent_invalid'] = False