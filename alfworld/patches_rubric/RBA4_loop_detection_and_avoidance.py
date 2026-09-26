# TARGET: Address failures where the agent falls into loops by revisiting places/objects with no success. Implement a simple loop detection and avoidance strategy.
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
    Update the state after executing each step to improve future action selection.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""
    
    if 'visited_places' not in state:
        state['visited_places'] = {}
    location_key = (observation, action)
    state['visited_places'][location_key] = state['visited_places'].get(location_key, 0) + 1

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

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a fallback action that minimizes revisiting locations with repetitive actions.
    Avoid already visited places-action pairs from past failures.
    """
    if 'visited_places' in state:
        # Filter admissible actions to avoid loops
        admissible_filtered = [action for action in admissible if state['visited_places'].get((state.get('last_observation', ''), action), 0) < 2]
        if admissible_filtered:
            return admissible_filtered[0]  # Return first valid non-looping action
    return 'look'  # the default fallback action