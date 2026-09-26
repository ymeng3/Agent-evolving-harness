HISTORY_LENGTH = 6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Enhanced retry mechanism with emphasis on learning from prior failures and modifying retry temperature adaptively.
    """
    if attempt == 1:
        extra_instruction = (
            "Remember that successful actions often follow patterns similar to this: {state.get('action_guide', '')}. "
            "Focus on these patterns."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.55}
    elif attempt == 2:
        extra_instruction = (
            "You've attempted actions before and learned from them. Choose based on that knowledge, specifically "
            "adhering to admissible actions that align with previously successful choices."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Recalling past successful actions might guide current decisions: {action_guide}."
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
    Extend the state information with successful actions to allow for better decision-making.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)

    # Induce patterns from successful actions to guide future attempts
    if len(state['action_success']) > 3:
        state['action_guide'] = action