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
    # Initialize visited_actions in state if it doesn't exist
    if "visited_actions" not in state:
        state["visited_actions"] = set()
    
    # Add the action to the visited actions
    state["visited_actions"].add(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Filter admissible actions to avoid those already taken
    new_actions = [action for action in admissible if action not in state.get("visited_actions", set())]
    if new_actions:
        return new_actions[0]  # Return the first new action
    return 'look'  # Fallback to 'look' if all admissible actions have been tried