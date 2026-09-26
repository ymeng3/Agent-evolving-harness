HISTORY_LENGTH = 8
TEMPERATURE = 0.6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with a more detailed action guidance focusing on the observable context.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nTip: Previous successful actions were similar to: {action_guide}. Consider your current position and constraints."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance based on successful choice
            state["action_guide"] = ",".join(set(state.get("action_guide", "").split(',') + [action]))
            return action
    # Default fallback action when no valid action is found
    return "look around"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the history of successful actions for consistent decision-making support.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        all_success_actions = set(state['action_success'])
        if len(all_success_actions) > 3:
            state['action_guide'] = ",".join(all_success_actions)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instruction on retries with enhanced focus on current observation and action history context.
    """
    extra_instruction = (
        "Recall the previously successful actions under similar conditions. Focus on choosing from the admissible options based on your current observation context."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None