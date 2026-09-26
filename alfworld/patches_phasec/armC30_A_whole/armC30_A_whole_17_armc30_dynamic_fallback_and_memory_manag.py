HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "last_actions" not in state:
        state["last_actions"] = []
    
    # Keep track of a limited action history
    state["last_actions"] = (state.get("last_actions", []) + [action])[-5:]

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer actions different from the recent past as fallback
    recent_actions = set(state.get("last_actions", []))
    for action in admissible:
        if action not in recent_actions:
            return action
    # If all admissible actions were recently executed, default to the first admissible
    return admissible[0]