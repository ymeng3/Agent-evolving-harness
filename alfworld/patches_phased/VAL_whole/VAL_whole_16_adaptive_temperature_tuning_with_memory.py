HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Dynamically adjust temperature based on attempt and recent episode success status stored in state
    base_temperature = 0.5
    extra_instruction = "Your last action wasn't valid. Please choose from the admissible actions listed."
    
    if attempt == 1:
        state['failed_attempts'] = state.get('failed_attempts', 0) + 1
        temperature = base_temperature - min(0.2, 0.05 * state['failed_attempts'])
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    
    elif attempt == 2:
        state['failed_attempts'] = state.get('failed_attempts', 0) + 1
        temperature = base_temperature - min(0.3, 0.05 * state['failed_attempts'])
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Reset failed attempts counter when valid action occurs
    state['failed_attempts'] = 0