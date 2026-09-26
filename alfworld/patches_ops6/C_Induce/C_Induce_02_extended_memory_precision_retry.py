HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    """
    Incorporate past successful actions if any exist in the current context to guide decision-making.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider repeating actions that led to success: {action_guide}."
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
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update state after executing each step to include memory of successful actions.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        if len(state['action_success']) > 3:
            state['action_guide'] = action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Adjust retry instructions to improve alignment with successful past actions and focus on admissible actions.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall previous successful actions and focus on the current admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action that aligns with prior successful instances from the admissible list."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None