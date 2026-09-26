HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """
    Add a reminder to consider past successful actions for guidance.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Previous successful actions suggest: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["action_guide"] = action  # Update guidance based on success
            return action
    return "look"  # Updated default fallback action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide clear instruction and adjust temperature on retries to focus on admissible actions.
    """
    extra_instruction = (
        "Your last action was invalid. Focus on selecting a valid option from the admissible actions list."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""