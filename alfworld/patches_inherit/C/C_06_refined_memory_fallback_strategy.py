HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """Update memory with recent action to detect loops."""
    if "actions_history" not in state:
        state["actions_history"] = []

    state["actions_history"].append(action)
    # Keep the latest 20 actions only for loop detection
    if len(state["actions_history"]) > 20:
        state["actions_history"].pop(0)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    """Choose fallback action, avoiding recent actions to reduce looping."""
    recent_actions = set(state.get("actions_history", [])[-5:])  # Check the last 5 actions for loops
    for action in admissible:
        if action not in recent_actions:
            return action
    return "look"  # Default to 'look' if all fallback options were recently attempted