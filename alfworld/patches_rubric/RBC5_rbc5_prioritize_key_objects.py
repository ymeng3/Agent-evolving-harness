# TARGET: Enhance task understanding and goal alignment by prioritizing key objects
def format_prompt(prompt: str, state: dict) -> str:
    """
    Modify the prompt to emphasize key objects related to the task's goals,
    aiming to improve task understanding and goal alignment.
    """
    task_related_objects = state.get("task_related_objects", "")
    if task_related_objects:
        prompt += f"\nImportant: Focus on interacting with objects related to your task: {task_related_objects}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state with information about task-related objects,
    extracted from the task description or observations, to aid future prompts.
    """
    if "task_description" not in state:
        # Assume the task_description is provided or can be derived early on
        state["task_description"] = observation
    
    if "task_related_objects" not in state:
        # Extract objects directly related to task from task description or updates
        extract_objects = lambda desc: [obj for obj in ['plate', 'mug', 'remotecontrol', 'toiletpaper'] if obj in desc]
        task_related_objects = extract_objects(state["task_description"])
        state["task_related_objects"] = ", ".join(task_related_objects)