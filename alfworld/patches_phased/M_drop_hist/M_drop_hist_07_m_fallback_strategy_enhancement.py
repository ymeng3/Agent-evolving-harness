from collections import defaultdict

HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["action_history"] = []
    
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
    
    state["action_history"].append((observation, action))
    
    if "take" in action:
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        object_placed = action.split("place ")[1]
        if object_placed in state["carried_objects"]:
            state["carried_objects"].remove(object_placed)
    
    if "receptacle_revisit_counts" not in state:
        state["receptacle_revisit_counts"] = defaultdict(int)
    
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize looking around if available, to recalibrate the environment understanding
    if 'look' in admissible:
        return 'look'
    
    # Try to repeat the last successful action if applicable
    if state.get("action_history"):
        last_action = state["action_history"][-1][1]
        if last_action in admissible:
            return last_action
    
    # Fallback to the first admissible action
    return admissible[0]