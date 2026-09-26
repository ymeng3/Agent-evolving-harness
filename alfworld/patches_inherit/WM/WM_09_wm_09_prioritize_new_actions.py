HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Prioritize selecting a new action that hasn't been recently attempted."
    
    if 'recent_actions' not in state:
        state['recent_actions'] = []
        
    # Keep track of all attempted actions
    state['recent_actions'].append(action)
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Clear the list if it gets too long to maintain only the most recent history
    if 'recent_actions' in state and len(state['recent_actions']) > 3:
        state['recent_actions'].pop(0)