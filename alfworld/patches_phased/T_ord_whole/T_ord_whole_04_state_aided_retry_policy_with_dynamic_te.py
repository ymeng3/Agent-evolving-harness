HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    state_temperature_key = "temperature_adjustment"
    
    # Calculate effective temperature based on attempts and state adjustment
    effective_temperature = max(0.2, 0.3 - attempt * (state.get(state_temperature_key, 0.05)))
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": effective_temperature}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": effective_temperature}
    
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Adjust temperature based on history signals
    history_pattern = ["look", "examine"]
    if any(action in history_pattern and action not in state.get("recent_actions", []) for action in history_pattern):
        state["temperature_adjustment"] = 0.10
    else:
        state["temperature_adjustment"] = 0.05
    
    # Update recent actions
    state["recent_actions"] = (state.get("recent_actions", []) + [action])[-HISTORY_LENGTH:]