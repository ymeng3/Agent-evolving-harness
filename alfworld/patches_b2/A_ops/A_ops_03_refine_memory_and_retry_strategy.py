HISTORY_LENGTH = 7

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Remember this action if it was successful
            if 'successful_actions' not in state:
                state['successful_actions'] = set()
            state['successful_actions'].add(action)
            return action
    # Fallback to 'look' if no valid action is found
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Hint the model to focus on admissible actions
        instruction = "Your previous action was not admissible. "
        if action in state.get('successful_actions', set()):
            instruction += f"Avoid repeating ineffective actions like '{action}' when possible. "
        return {"extra_instruction": instruction, "temperature": 0.3}
    elif attempt == 2:
        # Reinforce necessity of choosing admissible actions
        return {"extra_instruction": "Focus on choosing actions strictly from the admissible list.", "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory based on the outcome of the action
    if "successfully" in next_observation:
        state.setdefault("memory_notes", []).append(f"Action '{action}' worked.")
    elif "cannot" in next_observation:
        state.setdefault("memory_notes", []).append(f"Action '{action}' was ineffective.")