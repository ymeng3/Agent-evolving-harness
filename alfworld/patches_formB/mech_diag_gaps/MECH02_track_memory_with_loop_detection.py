HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize state if not already done
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
        state['action_history'] = []

    # Assuming receptacles are mentioned in the observations
    receptacle_keywords = ['cabinet', 'fridge', 'table', 'counter', 'shelf']
    observed_receptacles = set(
        word for word in observation.split() if any(keyword in word for keyword in receptacle_keywords)
    )

    # Update visited receptacles
    state['visited_receptacles'].update(observed_receptacles)

    # Log the action
    state['action_history'].append(action)
    
    # Limit action history to a reasonable length to avoid memory bloat
    if len(state['action_history']) > 50:
        state['action_history'].pop(0)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Make sure to choose an action from the given current admissible actions list.", "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": f"Your admissible actions are: {admissible}. Please select a valid action with consideration to already visited receptacles: {state.get('visited_receptacles', {})}", "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Attempt to choose an action that hasn't been repeated recently
    recent_actions = set(state.get('action_history', [])[-3:])
    available_actions = [action for action in admissible if action not in recent_actions]

    if available_actions:
        return available_actions[0]  # Return the first non-recent action
    return 'look'  # Fallback to 'look' if all are recent