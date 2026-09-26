HISTORY_LENGTH = 8

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action was invalid. Please carefully choose one from the admissible actions provided."
    temperature = 0.5
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    if "carried_objects" not in state:
        state["carried_objects"] = set()
    if "action_history" not in state:
        state["action_history"] = []
    if "object_interactions" not in state:
        state["object_interactions"] = defaultdict(int)
    
    # Update visited receptacles
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
    
    state["action_history"].append((observation, action))
    
    # Track object interactions based on actions
    action_parts = action.split()
    if "take" in action_parts:
        object_taken = action_parts[action_parts.index("take") + 1]
        state["carried_objects"].add(object_taken)
        state["object_interactions"][object_taken] += 1
        
    if "place" in action_parts:
        object_placed = action_parts[action_parts.index("place") + 1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
            state["object_interactions"][object_placed] += 1        
    
    state["object_interactions"] = {obj: count for obj, count in state["object_interactions"].items() if count > 0}