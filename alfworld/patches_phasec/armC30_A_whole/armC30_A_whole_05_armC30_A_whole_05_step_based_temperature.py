HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    step_temperature = max(0.1, 0.5 - state.get("current_step", 0) * 0.01)
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": step_temperature}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": step_temperature - 0.1}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state["current_step"] = state.get("current_step", 0) + 1