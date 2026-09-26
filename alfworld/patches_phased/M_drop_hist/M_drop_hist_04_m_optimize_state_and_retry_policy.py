HISTORY_LENGTH = 3
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on selecting one of the admissible actions. Consider your current context."
    if attempt == 1:
        # Restore temperature to default after first attempt
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        # Lower temperature further to reduce randomness
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state on the first step
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["action_history"] = []
        state["carried_objects"] = set()
    
    # Update the visited receptacles
    if "receptacle" in observation and state["visited_receptacles"] is not None:
        state["visited_receptacles"].add(observation)
    
    state["action_history"].append((observation, action))
    
    # Update carried objects based on action taken
    if "take" in action:
        # Extract the object from the action string
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        # Extract the object from the action string
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)