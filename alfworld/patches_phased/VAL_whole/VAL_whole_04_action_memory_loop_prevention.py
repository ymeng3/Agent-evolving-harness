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
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    recent_actions = set(state["action_history"][-3:]) if "action_history" in state else set()
    for action in admissible:
        if action not in recent_actions:
            return action
    return admissible[0]  # Fallback to any admissible action if all are recent