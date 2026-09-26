TEMPERATURE = 0.5
HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update memory to maintain a list of past actions to detect repetitions.
    """
    if "past_actions" not in state:
        state["past_actions"] = collections.deque(maxlen=3)
    state["past_actions"].append(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Retry strategy with decreasing temperatures upon inadmissible action and an extra prompt instruction.
    """
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if action in state.get("past_actions", []):
        # If we are repeating an invalid action, change the extra instruction
        if attempt == 1:
            return {"extra_instruction": "Avoid repeating actions unnecessarily. Consider alternative strategies.", "temperature": 0.3}
        elif attempt == 2:
            return {"extra_instruction": "Your repeated action is invalid again. Try a new approach.", "temperature": 0.2}
    else:
        if attempt == 1:
            return {"extra_instruction": extra_instruction, "temperature": 0.3}
        elif attempt == 2:
            return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Fallback strategy to choose the least recent action when no admissible action is found.
    """
    # Preferably choose an action that has not been tried recently
    recent_actions = set(state.get("past_actions", []))
    for action in admissible:
        if action not in recent_actions:
            return action
    return admissible[0]  # If all actions were recent, choose the first admissible action