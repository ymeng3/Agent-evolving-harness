def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track visited locations and objects picked up
    if "visited_locations" not in state:
        state["visited_locations"] = set()
    if "picked_objects" not in state:
        state["picked_objects"] = set()
    
    if "in room" in observation:
        state["visited_locations"].add(observation)
    
    if "holding" in next_observation and not "nothing" in next_observation:
        state["picked_objects"].add(next_observation.split("holding ")[-1])

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize actions that interact with visited locations or picked objects
    location_based_actions = [action for action in admissible if any(vis in action for vis in state.get("visited_locations", []))]
    object_based_actions = [action for action in admissible if any(obj in action for obj in state.get("picked_objects", []))]

    if location_based_actions:
        return location_based_actions[0]
    if object_based_actions:
        return object_based_actions[0]
    
    # Default fallback is 'look' if no other preference is determined
    return 'look'