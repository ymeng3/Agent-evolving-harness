HISTORY_LENGTH = 12
TEMPERATURE = 0.35

def format_prompt(prompt: str, state: dict) -> str:
    # Adding observation insights to the prompt
    if "observed_objects" not in state:
        state["observed_objects"] = set()

    new_observations = set()    
    if "object" in prompt:
        observations = prompt.split("observation is: ")[1].split('\n')[0]
        objects = [obj.strip() for obj in observations.split(',') if "object" in obj]
        new_observations = set(objects)
        state["observed_objects"].update(new_observations)
    
    # Enhance the prompt with previously observed objects
    observed_summary = "You have previously noticed these objects: " + ", ".join(state["observed_objects"]) + "."
    enhanced_prompt = f"{prompt}\n{observed_summary}"
    return enhanced_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Make sure your next action is one of the admissible actions."
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