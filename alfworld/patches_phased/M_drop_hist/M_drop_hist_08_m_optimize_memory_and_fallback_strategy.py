HISTORY_LENGTH = 3
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    """
    Optimize the prompt formatting to include additional state information.
    """
    
    # Add any additional state information to prompt for enhanced guidance
    additional_info = ""
    if state.get("carried_objects"):
        additional_info += f"\nCurrently carried objects: {', '.join(state['carried_objects'])}."
    
    return prompt + additional_info

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please select an admissible action from the list provided."
    if attempt < 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    return None

from collections import defaultdict

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory state on the first step
    state.setdefault("visited_receptacles", set())
    state.setdefault("carried_objects", set())
    state.setdefault("action_history", [])
    
    if "receptacle" in observation:
        state["visited_receptacles"].add(observation.split()[0])

    state["action_history"].append((observation, action))
    
    # Update carried objects based on action
    if "take" in action:
        object_taken = action.split("take ")[1]
        state["carried_objects"].add(object_taken)
        
    if "place" in action:
        object_placed = action.split("place ")[1]
        state["carried_objects"].discard(object_placed)
    
    # Track revisits to receptacles
    state.setdefault("receptacle_revisit_counts", defaultdict(int))
    for receptacle in state["visited_receptacles"]:
        state["receptacle_revisit_counts"][receptacle] += 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the most logical fallback action, improving from default 'look'
    for action in admissible:
        if "take" in action or "place" in action:
            return action  # Prioritize taking or placing actions as fallback
    return admissible[0] if admissible else "look"