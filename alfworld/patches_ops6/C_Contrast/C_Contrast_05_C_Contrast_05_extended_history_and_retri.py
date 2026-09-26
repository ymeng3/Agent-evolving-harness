HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    """
    Add instructions from previous successful actions to assist in decision-making.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Refer to previously successful actions: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update state with the chosen action for future guidance
            state["action_guide"] = action
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update state with successful actions for future reference.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide further guidance and adjust temperature on retries for improved action selection.
    """
    extra_instruction = "Your last action was invalid. Choose wisely from the admissible actions provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None