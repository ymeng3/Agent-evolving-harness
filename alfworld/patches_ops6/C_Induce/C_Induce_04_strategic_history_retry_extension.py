HISTORY_LENGTH = 17

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with additional guidance based on previous successful patterns.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider past actions that led to success: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance only when using a successful choice
            state["action_guide"] = action
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to record successful actions.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        # Guide with most recent successful action
        if len(state['action_success']) > 0:
            state['action_guide'] = state['action_success'][-1]

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Apply iterative retry strategies with clear focus on admissible options and previously effective actions.
    """
    if attempt == 1:
        extra_instruction = (
            "Focus on the admissible actions and past successful experiences."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        extra_instruction = (
            "Prioritize actions closely related to earlier successes within admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None