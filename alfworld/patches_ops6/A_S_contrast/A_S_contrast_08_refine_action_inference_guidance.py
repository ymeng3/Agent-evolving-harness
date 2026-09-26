HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nRemember: Successful actions in similar situations were: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance optimistically based on successful choice
            state["action_guide"] = action
            return action
    # Fall back to a typical exploration action when no valid action is found
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 2 else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Customize instructions and slight temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall previous guidance on successful actions. Prioritize choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        extra_instruction = (
            "Focus on selecting an admissible action that best matches past successful patterns."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None