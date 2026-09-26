HISTORY_LENGTH = 6

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
    Update the state after executing each step to improve future action selection by tracking successful actions.
    """
    if 'successful_actions_counter' not in state:
        state['successful_actions_counter'] = {}
    
    if "successfully" in next_observation:
        state['successful_actions_counter'][action] = state['successful_actions_counter'].get(action, 0) + 1
        # Update action guide based on the most frequently successful action
        if len(state['successful_actions_counter']) > 0:
            state['action_guide'] = max(state['successful_actions_counter'], key=state['successful_actions_counter'].get)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on frequent successful actions. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with historically successful actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None