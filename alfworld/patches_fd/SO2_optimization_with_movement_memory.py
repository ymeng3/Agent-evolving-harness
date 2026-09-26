# TARGET: unspecified
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on previous successful actions and unused areas.
    """
    action_guide = state.get("action_guide", "")
    unexplored_areas = state.get("unexplored_areas", [])
    prompt += f"\nUnexplored areas: {', '.join(unexplored_areas)}." if unexplored_areas else ""
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    action = match.group(1).strip().lower() if match else "examine"
    if action in admissible:
        if state.get("current_location") and state["current_location"] in state.get("unexplored_areas", []):
            state["unexplored_areas"].remove(state["current_location"])
        # Update based on successful choice
        state["action_guide"] = action
        return action
    return "examine"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Adjust instructions and temperature with emphasis on unexplored areas.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on successful actions. Also, focus on unexplored areas for finding necessary objects."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with previous successes. Explore unexplored areas."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Track visited spaces to avoid unnecessary revisits and focus on unexplored areas.
    """
    if "unexplored_areas" not in state:
        state["unexplored_areas"] = [f"cabinet {i}" for i in range(1, 10)] + [f"drawer {i}" for i in range(1, 10)]
    
    if action.startswith("go to"):
        state["current_location"] = action.split("go to ")[-1]
    
    if "successfully" in next_observation or "picked up" in next_observation or "moved" in next_observation:
        state['action_guide'] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Prioritize going to unexplored areas if any are left; otherwise, fallback to 'look'.
    """
    unexplored = state.get("unexplored_areas", [])
    for area in unexplored:
        goto_action = f"go to {area}"
        if goto_action in admissible:
            return goto_action
    return "look"