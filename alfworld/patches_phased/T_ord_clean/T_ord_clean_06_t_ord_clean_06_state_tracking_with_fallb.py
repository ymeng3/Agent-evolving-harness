HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize state keys for tracking
    state.setdefault('action_history', set())
    state.setdefault('objectives', [])

    # Track unique actions taken
    state['action_history'].add(action)
    
    # Update objectives if a relevant action occurs
    if "place" in action and "successfully" in next_observation:
        state['objectives'].append("completed_placement")
    if "pick" in action and "successfully" in next_observation:
        state['objectives'].append("picked_object")

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize untried admissible actions, else fallback to 'look'
    untried_actions = [act for act in admissible if act not in state['action_history']]
    return untried_actions[0] if untried_actions else 'look'