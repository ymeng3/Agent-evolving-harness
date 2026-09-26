HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        last_observation, last_action = state.get('last_step', ('', ''))
        
        if last_action == action:
            extra_instruction = (
                "The action you repeated is not effective in this context. "
                "Analyze previous observations and actions to select a more suitable option. "
                "Avoid repeating the same action if it did not work the first time. "
            )
            state['retry'] = True
            return {"extra_instruction": extra_instruction}
        
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_step'] = (next_observation, action)
    if state.get('retry', False):
        state['retry'] = False