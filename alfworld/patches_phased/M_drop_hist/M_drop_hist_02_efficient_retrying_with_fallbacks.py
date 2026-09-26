from collections import defaultdict

HISTORY_LENGTH = 4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = f"Your last action '{action}' wasn't valid. Carefully select one of these actions: {', '.join(admissible)}."
    if attempt == 1 or attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer "look" as a safe fallback if available
    if "look" in admissible:
        return "look"
    # If "look" is unavailable, fall back to any other admissible action
    return admissible[0] if admissible else ""

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
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        # Extract the object from the action string
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
    
    # Keep track of the number of revisits to each receptacle
    if "receptacle_revisit_counts" not in state:
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1