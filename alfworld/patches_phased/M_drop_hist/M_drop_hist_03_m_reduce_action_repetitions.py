HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Avoid repeating the same invalid action."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
        state["carried_objects"] = set()
        state["action_history"] = []
    
    state["action_history"].append(action)

    if len(state["action_history"]) > 3:
        state["action_history"].pop(0)

    if "receptacle" in observation:
        state["visited_receptacles"].add(observation)
    
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
    recent_actions = state.get("action_history", [])
    
    for action in admissible:
        if action not in recent_actions:
            return action
    
    return admissible[0]