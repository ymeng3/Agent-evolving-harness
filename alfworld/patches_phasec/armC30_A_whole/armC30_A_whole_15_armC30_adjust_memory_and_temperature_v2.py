HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = collections.defaultdict(int)
    
    # Update action occurrences
    state['action_count'][action] += 1

    # Track observation path
    if 'recent_observation' not in state:
        state['recent_observation'] = []
    
    state['recent_observation'].append(observation)
    if len(state['recent_observation']) > 5:
        state['recent_observation'].pop(0)