HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting an admissible action. Consider recent observations."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.1}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        
    # Extract receptacles mentioned in the current observation
    extract_items = lambda obs: set(filter(None, map(str.strip, obs.lower().split(':')[1:])))
    state["visited_receptacles"].update(extract_items(observation))

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize visiting unvisited receptacles as fallback action
    for action in admissible:
        receptacle = action.replace('open', '').strip()
        if receptacle not in state.get("visited_receptacles", set()):
            return action
    return admissible[0]  # Default to the first admissible action if no unvisited receptacle found