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

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """E2: on a failed retry, do not repeat the same hint; name three concrete admissible commands and require one verbatim."""
    picks = []
    for a in admissible:
        if a.startswith("go to ") and len(picks) < 1: picks.append(a)
    for a in admissible:
        if (a.startswith("open ") or a.startswith("take ")) and len(picks) < 2 and a not in picks: picks.append(a)
    for a in admissible:
        if a != "look" and a not in picks and len(picks) < 3: picks.append(a)
    if attempt == 1:
        return {"extra_instruction": "Your last reply did not end with a valid action. Reply with exactly one admissible action inside <action></action>, for example: " + ", ".join(picks) + ".", "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": "Copy one of these admissible actions verbatim into <action></action>: " + " | ".join(picks) + ".", "temperature": 0.3}
    return None