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
    """Update the memory with changes in the environment and previously performed actions."""
    if "changes" not in state:
        state["changes"] = []
    
    # Determine changes between observations
    change_detected = next_observation != observation
    state["changes"].append((observation, action, change_detected))
    
    # Maintain a limited memory size
    if len(state["changes"]) > 50:  # Arbitrary memory size limit
        state["changes"].pop(0)