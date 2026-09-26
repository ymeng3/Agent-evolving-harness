HISTORY_LENGTH = 15
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "recent_actions" not in state:
        state["recent_actions"] = collections.deque(maxlen=5)
    state["recent_actions"].append(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Consider using a different strategy. Focus on selecting one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        recent_actions = ", ".join(state.get("recent_actions", []))
        additional_instruction = f"Recent actions taken: {recent_actions}. Avoid repeating them."
        return {"extra_instruction": extra_instruction + " " + additional_instruction, "temperature": 0.2}
    return None