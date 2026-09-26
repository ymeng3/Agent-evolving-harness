HISTORY_LENGTH = 3
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Add previous carried objects info to the prompt for better reasoning
    carried_objects_info = f"Currently carried objects: {', '.join(state.get('carried_objects', []))}."
    return f"{carried_objects_info}\n{prompt}"

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Extract action from the formatted response
    action_match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            return action
    return "look"  # Default fallback if nothing is found

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Ensure you are selecting from the admissible actions. Consider current carried items, if applicable."
    temperature_adjustment = 0.05
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE + temperature_adjustment}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - temperature_adjustment}
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

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Fallback strategy attempts to choose a sensible action based on history
    if state.get("carried_objects"):
        for action in admissible:
            if "place" in action:
                return action
    return "look"