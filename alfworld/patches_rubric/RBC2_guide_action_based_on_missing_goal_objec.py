# TARGET: Improve task understanding and goal alignment by guiding the agent towards missing objects in the scene.
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance towards achieving the task goal based on missing objects.
    """
    missing_objects_guide = state.get("missing_objects_guide", "")
    if missing_objects_guide:
        prompt += f"\nHint: Focus on areas likely to contain the missing objects needed to complete your task: {missing_objects_guide}."

    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."

    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance based on successful choice
            state["action_guide"] = action
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    """
    if 'action_success' not in state:
        state['action_success'] = []

    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""

    # Detect missing goal objects to guide exploration
    task_context = state.get("task_context", {})
    if not task_context:
        task_context["goal_object"] = "needed objects based on the task description" # This is a placeholder
        state["task_context"] = task_context

    # Update guide for missing objects
    if "You see" in next_observation:
        observed_items = next_observation.lower()
        if task_context["goal_object"] not in observed_items:
            state["missing_objects_guide"] = "search other receptacles or locations"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on missing goal objects and successful actions. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with finding and using missing objects."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None