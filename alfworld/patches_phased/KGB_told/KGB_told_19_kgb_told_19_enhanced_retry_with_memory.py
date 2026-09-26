HISTORY_LENGTH = 7
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Please carefully choose an action from the admissible actions."
    if attempt == 1:
        state['last_attempt'] = response
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    elif attempt == 2:
        if state.get('last_attempt', '') != response:
            return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()
    state['visited'].add((observation, action, next_observation))

def choose_fallback(admissible: list[str], state: dict) -> str:
    if 'look' in admissible:
        return 'look'
    return random.choice(admissible)