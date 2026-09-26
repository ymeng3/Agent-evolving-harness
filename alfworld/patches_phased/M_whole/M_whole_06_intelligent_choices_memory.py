HISTORY_LENGTH = 10
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None


from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state on the first step
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["action_history"] = []
    
    # Update the visited receptacles and action history
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
    
    state["action_history"].append((observation, action))
    
    # Update carried objects based on action
    if "take" in action:
        # Extract the object from the action string
        object_taken = action.split("take ")[1].strip()
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        # Extract the object from the action string
        object_placed = action.split("place ")[1].strip()
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
    
    # Keep track of the number of revisits to each receptacle
    if "receptacle_revisit_counts" not in state:
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose a fallback action based on the least visited receptacle
    if "receptacle_revisit_counts" in state:
        unvisited_receptacles = [rec for rec in admissible if rec not in state["visited_receptacles"]]
        if unvisited_receptacles:
            return unvisited_receptacles[0]
    
    # Default to 'look' if all receptacles have been visited
    return 'look'