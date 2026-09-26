HISTORY_LENGTH = 15
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Double-check the admissible actions and choose wisely."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    recent_receptacles = state.get('recent_receptacles', set())
    
    # Identify receptacles or locations from the observation
    matched_receptacles = {word for word in observation.lower().split() if 'receptacle' in word or 'location' in word}
    
    # Update state with new receptacles observed
    recent_receptacles.update(matched_receptacles)
    state['recent_receptacles'] = recent_receptacles

def format_prompt(prompt: str, state: dict) -> str:    
    # Incorporate notes on receptacles and locations observed
    receptacles_info = ""
    if state.get('recent_receptacles'):
        receptacles_info = f" Previously observed receptacles include: {', '.join(state['recent_receptacles'])}."
        
    return f"{prompt}{receptacles_info}"