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
    visited_actions_key = "visited_actions"
    if visited_actions_key not in state:
        state[visited_actions_key] = set()
    
    state[visited_actions_key].add(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    visited_actions = state.get("visited_actions", set())

    unvisited_actions = [action for action in admissible if action not in visited_actions]
    
    return unvisited_actions[0] if unvisited_actions else admissible[0]