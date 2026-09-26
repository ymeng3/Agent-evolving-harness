HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed and analyze the action context."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()
    if action != 'look':  # assuming 'look' updates state with overly frequent actions
        state['visited'].add(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer actions that haven't been visited yet, if possible
    unvisited = [action for action in admissible if action not in state['visited']]
    return unvisited[0] if unvisited else 'look'