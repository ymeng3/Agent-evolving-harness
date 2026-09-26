HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    t = prompt.lower()
    if "heat" in t.split("task")[-1][:200] if "task" in t else False:
        prompt += "\nNote: to heat an object you must be HOLDING it, go to the microwave, and use the command 'heat <object> with microwave 1'. Do not put the object into the microwave."
    elif "cool" in t.split("task")[-1][:200] if "task" in t else False:
        prompt += "\nNote: to cool an object you must be HOLDING it, go to the fridge, and use the command 'cool <object> with fridge 1'. Do not put the object into the fridge."
    elif "clean" in t.split("task")[-1][:200] if "task" in t else False:
        prompt += "\nNote: to clean an object you must be HOLDING it, go to the sinkbasin, and use the command 'clean <object> with sinkbasin 1'. Do not put the object into the sink."
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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on successful actions. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with previous successes."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None