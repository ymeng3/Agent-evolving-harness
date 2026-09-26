HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_adjustments = {1: 0.25, 2: 0.15}
    if attempt in temperature_adjustments:
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustments[attempt]}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "recent_actions" not in state:
        state["recent_actions"] = []

    # Track last 3 actions to detect repetition patterns
    state["recent_actions"].append(action)
    if len(state["recent_actions"]) > 3:
        state["recent_actions"].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Avoid repeating the last action if possible
    recent_actions = state.get("recent_actions", [])
    non_repeated_actions = [action for action in admissible if action not in recent_actions]
    
    return non_repeated_actions[0] if non_repeated_actions else admissible[0]