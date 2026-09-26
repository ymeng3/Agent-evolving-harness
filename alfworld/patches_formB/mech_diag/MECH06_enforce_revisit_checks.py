HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'receptacle_visits' not in state:
        state['receptacle_visits'] = set()
        
    containers_visited = [word for word in next_observation.lower().split() if 'receptacle' in word]
    state['receptacle_visits'].update(containers_visited)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        if 'receptacle_visits' in state and len(state['receptacle_visits']) > 10:
            return {'extra_instruction': 'Consider exploring new areas to avoid repetitive actions in visited places.', 'temperature': 0.5}
    elif attempt == 2:
        return {'extra_instruction': 'Apply strategic reasoning to select actions that minimize revisiting.', 'temperature': 0.6}
    return None