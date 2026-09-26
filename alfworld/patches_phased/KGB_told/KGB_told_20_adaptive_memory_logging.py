HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Create a list to store actions and observations if not exists
    if "history" not in state:
        state["history"] = []
    # Add the current action and observation
    state["history"].append((observation, action, next_observation))
    # Keep memory to a reasonable length to prevent overflow
    if len(state["history"]) > 50:
        state["history"].pop(0)