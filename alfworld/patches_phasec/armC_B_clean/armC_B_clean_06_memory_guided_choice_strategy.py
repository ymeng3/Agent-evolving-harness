HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Maintain a set of visited observations for loop detection
    if "visited" not in state:
        state["visited"] = set()
    state["visited"].add(observation)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer unvisited actions to avoid loops
    for action in admissible:
        if action not in state.get("visited_actions", set()):
            return action
    # If all actions are visited, return the first admissible action
    return admissible[0]

    # Update memory of visited actions
    state.setdefault("visited_actions", set()).update(admissible)