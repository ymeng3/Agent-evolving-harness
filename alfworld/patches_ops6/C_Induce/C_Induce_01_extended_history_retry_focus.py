HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Review previous successful actions and focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Carefully select an action from admissible options closest to past successful actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None