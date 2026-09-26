# TARGET: Improve the detection and utilization of contextual clues in the task's state to enhance decision making and action relevance, reduce unnecessary repetition, and increase the likelihood of choosing ad
HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """
    Enhance the prompt with context-sensitive action guidance based on task type and previous successes.
    """
    task_type_hint = state.get("task_type_hint", "")
    action_guide = state.get("action_guide", "")
    
    if task_type_hint:
        prompt = f"Task Type: {task_type_hint}. " + prompt
    
    if action_guide:
        prompt += f"\nNote: Previous successful actions suggest trying: {action_guide}."
    
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["action_guide"] = action  # Update action guidance based on successful choice
            return action
    return "look"  # Default fallback action is more passive

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Memory retention focused on successful actions and deducing task type patterns.
    """
    if 'action_success' not in state:
        state['action_success'] = []

    if "successfully" in next_observation:
        state['action_success'].append(action)
        if len(state['action_success']) > 2:
            state['action_guide'] = state['action_success'][-1]

    # Identifying type of the task based on objects typically interacted with
    if "clean" in next_observation or "wash" in action:
        state['task_type_hint'] = "cleaning"
    elif "cool" in next_observation or "fridge" in action:
        state['task_type_hint'] = "cooling"
    elif "heat" in next_observation or "stove" in action:
        state['task_type_hint'] = "heating"
    elif "place" in next_observation:
        state['task_type_hint'] = "placing"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Adjust retry strategies by reinforcing the importance of admissible actions, with a gradual temperature decrease.
    """
    if attempt == 1:
        extra_instruction = "Ensure action is among admissible options and relate to previous learnings."
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        extra_instruction = "Select from admissible actions and be guided by what worked earlier."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Opt for a context-aware default action as a last resort.
    """
    for action in ["look", "examine"]:
        if action in admissible:
            return action
    return random.choice(admissible)