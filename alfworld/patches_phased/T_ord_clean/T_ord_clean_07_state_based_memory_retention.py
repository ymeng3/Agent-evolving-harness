HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if not 'visited_locations' in state:
        state['visited_locations'] = []
    
    # Keep track of visited locations based on observation data
    if "location:" in observation:
        location = observation.split("location:", 1)[1].strip()
        if location not in state['visited_locations']:
            state['visited_locations'].append(location)
    
    # Update memory for redundantly repeated actions and count of unique actions
    state['last_action'] = action
    state.setdefault('action_history', []).append(action)
    state['unique_actions'] = len(set(state['action_history']))

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = f"Your last action, '{action}', wasn't valid. "
    if attempt == 1:
        unique_action_text = f"You have selected {state.get('unique_actions', 0)} unique actions so far. "
        extra_instruction += "Focus on selecting one of the admissible actions listed. " + unique_action_text
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        location_text = f"You have visited {len(state.get('visited_locations', []))} locations. "
        extra_instruction += "Please try again with one of the admissible actions listed. " + location_text
        return {"extra_instruction": extra_instruction}
    return None