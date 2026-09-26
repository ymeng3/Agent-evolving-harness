HISTORY_LENGTH = 3
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The last action was not valid. Please choose from the given admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state on the first step
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["action_history"] = []
    
    # Update visited receptacles when specific cues are detected
    if "receptacle" in observation.lower():
        state["visited_receptacles"].add(observation)
    
    # Logging the action history with a capped history length to avoid overflow
    state["action_history"].append((observation, action))
    if len(state["action_history"]) > HISTORY_LENGTH:
        state["action_history"].pop(0)
    
    # Update carried objects based on the action keywords
    if "take" in action:
        object_taken = action.split("take ")[1] if "take " in action else ""
        if object_taken:
            state["carried_objects"].add(object_taken)
        
    if "place" in action:
        object_placed = action.split("place ")[1] if "place " in action else ""
        if object_placed and object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
    
    # Track revisiting of receptacles
    if "receptacle_revisit_counts" not in state:
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1