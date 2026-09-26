HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    Keep track of actions that led to success.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation and action not in state['action_success']:
        state['action_success'].append(action)
        if len(state['action_success']) > 1:
            state['action_guide'] = ", ".join(state['action_success'][-2:])

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    # Default fallback action when no valid action is found
    return "examine"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    Incorporate memory guidance to remind about successful past actions.
    """
    if attempt == 1:
        extra_instruction = (
            "Please focus on choosing from admissible actions while considering past successful actions for better alignment."
            f" Past successful actions: {state.get('action_guide', 'None')}."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            f"Reinforce past successes for more accurate decision-making. Actions to consider: {state.get('action_guide', 'None')}."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None