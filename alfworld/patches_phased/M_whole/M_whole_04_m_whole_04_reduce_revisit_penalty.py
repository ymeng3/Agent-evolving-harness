HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}  # Slightly decrease temperature for precision
    return None

from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["action_history"] = []
    
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
        
        # Reduce revisit penalty by only increasing revisit counts after a 'place' action
        if "place" in action:
            if "receptacle_revisit_counts" not in state:
                state["receptacle_revisit_counts"] = defaultdict(int)
            state["receptacle_revisit_counts"][observation] += 1
    
    state["action_history"].append((observation, action))
    
    if "take" in action:
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)