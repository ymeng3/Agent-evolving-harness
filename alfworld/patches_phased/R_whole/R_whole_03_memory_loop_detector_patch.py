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
    # Initialize memory if it doesn't exist
    if "visited" not in state:
        state["visited"] = set()
    if "repeat_count" not in state:
        state["repeat_count"] = 0
    
    # Record the (observation, action) pair
    current_state = (observation, action)
    if current_state in state["visited"]:
        state["repeat_count"] += 1
    else:
        state["visited"].add(current_state)
        state["repeat_count"] = 0

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Warn if there's a detected loop
    if state.get("repeat_count", 0) >= 2:
        return "look"  # Fallback to 'look' if potential loop detected
    return random.choice(admissible)