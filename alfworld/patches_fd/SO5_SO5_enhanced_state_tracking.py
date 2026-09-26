# TARGET: unspecified
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    Include cached locations and focus on unexplored areas.
    """
    action_guide = state.get("action_guide", "")
    location_guide = state.get("location_guide", "")
    if location_guide:
        prompt += f"\nNote: Consider checking locations with prior objects: {location_guide}."
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
    Cache locations of found objects for targeted search.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if 'location_cache' not in state:
        state['location_cache'] = set()
    
    if "successfully" in next_observation or "you see" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""
    
    if "you see" in next_observation:
        observed_items = re.findall(r"a (\w+ \d+)", next_observation)
        state['location_cache'].update(observed_items)
        if len(state['location_cache']) > 3:
            state['location_guide'] = ", ".join(list(state['location_cache'])[-3:])

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    Encourage revisiting locations with items.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on successful actions and object locations. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with previous successes. Consider locations with previous items."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None