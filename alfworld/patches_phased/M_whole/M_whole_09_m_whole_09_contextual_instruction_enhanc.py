HISTORY_LENGTH = 10

TEMPERATURE = 0.3


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Consider the task requirements: {task_description}"
    if attempt == 1:
        return {"extra_instruction": extra_instruction.format(task_description=state.get("task_description", "unknown task"))}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction.format(task_description=state.get("task_description", "unknown task"))}
    return None


def format_prompt(prompt: str, state: dict) -> str:
    # Extract task description from the prompt and store it in state for retry policy use
    task_description_start = prompt.find("Your task is to: ") + len("Your task is to: ")
    task_description_end = prompt.find("Prior to this step,")
    state["task_description"] = prompt[task_description_start:task_description_end].strip()
    return prompt


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