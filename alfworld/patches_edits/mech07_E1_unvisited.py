HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "objects_taken" not in state:
        state["objects_taken"] = set()
    if "family_verbs_issued" not in state:
        state["family_verbs_issued"] = set()

    # Track objects that have been taken or manipulated
    if "take" in action or "pick up" in action:
        object_taken = action.split()[-1]
        state["objects_taken"].add(object_taken)

    # Track verbs that correspond to task family-specific actions, e.g., clean, cool, etc.
    if any(verb in action for verb in ["clean", "cool", "heat"]):
        state["family_verbs_issued"].add(action)
    if action.startswith("go to "):
        state.setdefault("_visited", []).append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer "take" actions if not all objects necessary have been taken
    for action in admissible:
        if ("take" in action or "pick up" in action) and action.split()[-1] not in state["objects_taken"]:
            return action
    
    # If all objects are taken, prefer family-specific actions (e.g., clean, cool)
    for action in admissible:
        if "clean" in action or "cool" in action or "heat" in action:
            if action not in state["family_verbs_issued"]:
                return action

    visited = state.get('_visited', [])
    for action in admissible:
        if action.startswith('go to ') and action not in visited:
            return action
    for action in admissible:
        if action != 'look':
            return action
    return admissible[0]