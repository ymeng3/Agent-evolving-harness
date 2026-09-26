HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Records each successful action in the state at a specific key.
    if "completed_actions" not in state:
        state["completed_actions"] = []
        
    state["completed_actions"].append({
        "action": action,
        "observation": observation,
        "next_observation": next_observation
    })