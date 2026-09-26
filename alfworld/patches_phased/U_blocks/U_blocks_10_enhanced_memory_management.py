HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state["recent_actions"] = state.get("recent_actions", [])
    state["recent_actions"].append(action)

    # Keep track of visited locations or objects
    state["visited"] = state.get("visited", set())
    if "location" in observation:
        state["visited"].add(observation)

    # Maintain a maximum memory length to avoid unnecessary accumulation
    if len(state["recent_actions"]) > 20:
        state["recent_actions"].pop(0)
    
    if len(state["visited"]) > 50:
        state["visited"] = set(list(state["visited"])[-50:])