HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Please pick an admissible action from the list provided. Pay attention to previously visited areas."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None


from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state on the first step
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    # Update visited receptacles and their revisit counts
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
        state["receptacle_revisit_counts"][observation] += 1
    
    # Update carried objects based on action
    if "take" in action:
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
    
    # Maintain a short history log limited to current context
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append((observation, action))
    if len(state["action_history"]) > HISTORY_LENGTH:
        state["action_history"].pop(0)