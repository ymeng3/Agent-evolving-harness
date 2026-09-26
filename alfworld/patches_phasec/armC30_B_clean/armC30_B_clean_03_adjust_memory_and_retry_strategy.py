HISTORY_LENGTH = 8
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "The previous action was invalid. Please focus on choosing from the given admissible actions."
        temperature = 0.6
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    elif attempt == 2:
        extra_instruction = "Let's try once more. Be careful to pick a valid action."
        temperature = 0.7
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()
    state["visited"].add(observation)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the first admissible action not visited before
    unvisited = [action for action in admissible if action not in state.get("visited", set())]
    if unvisited:
        return unvisited[0]
    # Default to the first action in the list if all have been visited
    return admissible[0]