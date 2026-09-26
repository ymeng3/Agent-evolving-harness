HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action was invalid. Carefully choose one of the admissible actions."
    if attempt == 1:
        state.setdefault('retry_attempts', 0)
        state['retry_attempts'] += 1
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()
    state['visited'].add(observation)
    
    # Detect repeated or looped actions based on memory
    if 'retry_attempts' in state and state['retry_attempts'] > 2:
        fallback_action = next((a for a in ['explore', 'look', 'walk around'] if a in state['visited']), None)
        state['fallback_action'] = fallback_action if fallback_action else 'look'
    else:
        state['fallback_action'] = None

def choose_fallback(admissible: list[str], state: dict) -> str:
    return state['fallback_action'] if state.get('fallback_action') in admissible else 'look'