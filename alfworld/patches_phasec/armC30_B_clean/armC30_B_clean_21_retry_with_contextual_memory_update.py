HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    # Update the retry mechanism to adaptively give contextual instructions based on the attempt count
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": "Re-evaluate the context and ensure the action selection is logical and valid.", "temperature": 0.6}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store visited observations to provide contextual knowledge during retries
    if 'visited_observations' not in state:
        state['visited_observations'] = []
    state['visited_observations'].append(next_observation)

    # Occasionally clean redundant entries to avoid excessive memory usage
    if len(state['visited_observations']) > 20:
        state['visited_observations'] = state['visited_observations'][-20:]