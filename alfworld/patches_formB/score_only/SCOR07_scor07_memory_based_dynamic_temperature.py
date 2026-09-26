TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Record previous observations and actions to detect if stuck
    if 'recent_observations' not in state:
        state['recent_observations'] = collections.deque(maxlen=5)
    state['recent_observations'].append(next_observation)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Increase temperature for more exploration if caught in potential loop (same observation repeating)
    if attempt == 1 and 'recent_observations' in state:
        if len(set(state['recent_observations'])) == 1:  # suspect loop if all recent observations are identical
            return {
                "extra_instruction": " It seems like we're stuck in a loop. Let's try something different.",
                "temperature": min(TEMPERATURE + 0.2, 1.0)
            }
    return None