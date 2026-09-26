HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action was not valid. Please ensure your next action is one of the admissible actions. Consider the task requirements closely."
    if attempt == 1:
        # Providing a more assertive guidance for first retry.
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        # Lowering the temperature further to encourage more deterministic decisions.
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Ensure state tracking of repeated actions to prevent loop behavior.
    state.setdefault("recent_actions", []).append(action)
    if len(state["recent_actions"]) > 5:  # Keep the list to the last 5 actions.
        state["recent_actions"].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prevent repeating actions and choose a fallback that wasn't just tried.
    recent_actions = state.get("recent_actions", [])
    for action in admissible:
        if action not in recent_actions:
            return action
    return "look"  # Default fallback if all admissible actions were recently tried.