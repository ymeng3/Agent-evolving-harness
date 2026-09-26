def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize the set of visited receptacles if not present
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    
    # Detect if the current action involves a receptacle (e.g., examining, cleaning, cooling)
    receptacle_related_keywords = ['in', 'on', 'under', 'sink', 'fridge', 'shelf', 'table', 'counter']
    visited_receptacle_found = any(keyword in action.lower() for keyword in receptacle_related_keywords)

    # If the action is related to a receptacle, extract the object and add to visited receptacles
    if visited_receptacle_found:
        # This logic assumes that action is of the form "<verb> <object> [location/receptacle]"
        try:
            # Typically, the action format might be "put apple on the counter" or "clean plate in sink"
            split_action = action.lower().split()
            receptacle_index = [i for i, word in enumerate(split_action) if word in receptacle_related_keywords]

            if receptacle_index:
                # Select the first keyword that indicates a receptacle
                index = receptacle_index[0]
                state["visited_receptacles"].add(" ".join(split_action[index:index+3]))  # Include potential two-word receptacles
        except Exception:
            # In case of an extraction error, we simply don't add to visited for robustness
            pass

HISTORY_LENGTH = 5
TEMPERATURE = 0.4