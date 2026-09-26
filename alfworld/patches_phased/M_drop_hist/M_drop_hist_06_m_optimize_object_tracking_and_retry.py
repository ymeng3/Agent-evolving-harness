HISTORY_LENGTH = 3
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Your last action wasn't valid. Carefully choose from the listed admissible actions."}
    elif attempt == 2:
        return {"extra_instruction": "Focus on the admissible actions provided. Try selecting the most contextually relevant action."}
    return None


from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["object_interaction_history"] = defaultdict(list)
    
    if "receptacle" in observation and action.startswith("open"):
        state["visited_receptacles"].add(observation)
    
    if action.startswith("take"):
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        state["object_interaction_history"][object_taken].append("taken")
    
    if action.startswith("place"):
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
            state["object_interaction_history"][object_placed].append("placed")
    
    if "receptacle_revisit_counts" not in state:
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1