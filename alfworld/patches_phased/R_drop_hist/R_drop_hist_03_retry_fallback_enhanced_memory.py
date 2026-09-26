TEMPERATURE = 0.5
HISTORY_LENGTH = 4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Carefully choose from the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()
    state['visited'].add(observation)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to select an action not recently visited to avoid repetition
    for action in admissible:
        if action not in state.get('visited_actions', []):
            return action
    return 'look'