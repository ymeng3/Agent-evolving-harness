# TARGET: unspecified
HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts
    and enhance memory retention by stating what the agent should focus on avoiding.
    """
    action_guide = state.get("action_guide", "")
    avoidance_note = state.get("avoidance_note", "")
    
    guidance = ""
    if action_guide:
        guidance += f"Consider actions similar to previous successes: {action_guide}."
    if avoidance_note:
        guidance += f" Avoid repetitive exploration of {avoidance_note}."
    
    return f"{prompt}\nNote: {guidance}" if guidance else prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance based on successful choice
            state["action_guide"] = action
            # Reset avoidance note if action is successful
            state["avoidance_note"] = None
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection
    and avoid unnecessary repetition.
    """
    if "action_success" not in state:
        state["action_success"] = []
    if "visited_locations" not in state:
        state["visited_locations"] = set()

    current_place = observation.split("->")[-1].strip()  # Extract the current location, if possible.
    if current_place:
        if current_place in state["visited_locations"]:
            state["avoidance_note"] = current_place
        else:
            state["visited_locations"].add(current_place)
    
    if "successfully" in next_observation:
        state["action_success"].append(action)
        state["action_guide"] = action if len(state["action_success"]) > 3 else ""
    else:
        state["avoidance_note"] = current_place  # Update avoidance if no success.

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    Focus on avoiding repeated exploration of the same locations.
    """
    extra_instruction = (
        "Focus on new areas and avoid places previously explored unless necessary. "
        "Recall successful actions for better choices."
    )
    return {"extra_instruction": extra_instruction, "temperature": 0.6}

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Choose a fallback action. Prioritize 'examine' to gather more information,
    and avoid actions that lead to previously visited areas if not needed.
    """
    fallback_action = "examine"
    if fallback_action in admissible:
        return fallback_action
    
    for action in admissible:
        if state.get("avoidance_note") not in action:
            return action
    return admissible[0]