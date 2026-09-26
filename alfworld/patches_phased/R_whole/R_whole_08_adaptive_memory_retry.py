HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'seen_observations' not in state:
        state['seen_observations'] = set()
    state['seen_observations'].add(observation)
    
def choose_fallback(admissible: list[str], state: dict) -> str:
    # If a 'look' action is admissible, prioritize it as a fallback
    for action in admissible:
        if 'look' in action:
            return action
    # Otherwise, just return the first admissible action
    return admissible[0]