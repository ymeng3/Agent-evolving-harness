# TARGET: Address inefficiencies due to repeated "examine" actions that yield no progress.
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Add guidance to the prompt based on the history of actions.
    """
    action_guide = state.get("action_guide", "")
    examine_counter = state.get("examine_counter", 0)
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    if examine_counter > 1:
        prompt += "\nWarning: Multiple ineffective 'examine' actions taken. Focus on goal-related actions."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance based on successful choice
            state["action_guide"] = action
            if "examine" in action:
                state['examine_counter'] = state.get('examine_counter', 0) + 1
            else:
                state['examine_counter'] = 0
            return action
    # Default fallback action when no valid action is found
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state based on executed actions to reduce inefficiencies.
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