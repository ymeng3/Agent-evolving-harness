# TARGET: unspecified
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with additional guidance to prevent unnecessary re-cooling.
    """
    action_guide = state.get("action_guide", "")
    prompt += "\nRemember: Once an item is cooled, proceed directly to the destination for placement."
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
    Track if an item has been cooled to prevent redundant cooling actions.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""
    if "cool" in action and "successfully" in next_observation:
        state['cooled_item'] = True
    if "place" in action:
        # Once placed, reset cooling state
        state['cooled_item'] = False

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    If a cooled item is being recirculated, urge the prompt to focus on placement.
    """
    if attempt == 1:
        if state.get('cooled_item', False):
            extra_instruction = (
                "The item is already cooled. Proceed to place it in the desired location."
            )
        else:
            extra_instruction = (
                "Recall the guidance on successful actions. Focus on choosing from admissible options."
            )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        if state.get('cooled_item', False):
            extra_instruction = (
                "Place the already cooled item in the correct receptacle."
            )
        else:
            extra_instruction = (
                "Choose an action from admissible options that aligns with previous successes."
            )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose fallback action if no valid action is found even after retries.
    """
    return "look"