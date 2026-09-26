# TARGET: Enhance task understanding and goal alignment by reminding the agent of task requirements.
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the task requirements to keep the agent's actions goal-aligned.
    """
    task_requirements = state.get("task_requirements")
    if not task_requirements:
        import re
        task_match = re.search(r"task family: (\w+)-(\w+)-(\w+)-(\w+)", prompt)
        if task_match:
            _, target_obj, _, target_recep = task_match.groups()
            task_requirements = f"Find {target_obj} and place in {target_recep}."
            state["task_requirements"] = task_requirements
    if task_requirements:
        prompt += f"\nRemember: {task_requirements}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Inform agent of successful action for better awareness
            state["last_successful_action"] = action 
            return action
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    pass  # Keep this function without changes based on current failure analysis

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Reiterate task requirements on retries to improve goal alignment.
    """
    if attempt == 1 and "task_requirements" in state:
        extra_instruction = f"Recall the task: {state['task_requirements']} Consider the admissible actions."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2 and "task_requirements" in state:
        extra_instruction = f"Focus on finding the {state['task_requirements'].split()[1]}."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None