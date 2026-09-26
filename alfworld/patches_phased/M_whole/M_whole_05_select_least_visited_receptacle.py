HISTORY_LENGTH = 10

from collections import defaultdict

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
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
    visited_receptacles = state.get("visited_receptacles", set())
    revisit_counts = state.get("receptacle_revisit_counts", defaultdict(int))

    # Filter admissible actions to only those involving receptacles
    receptacle_actions = [action for action in admissible if any(receptacle in action for receptacle in visited_receptacles)]

    if receptacle_actions:
        # Select the action involving the least visited receptacle
        least_visited_action = min(receptacle_actions, key=lambda a: revisit_counts.get(a, 0))
        return least_visited_action

    return "look"