HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Make sure you select one of the admissible actions provided."
    # Introducing a dynamic temperature scaling based on the number of attempts and step count
    temperature_scaling_factor = 0.1 * max(1, min(10, state.get("step_count", 10) // 5))
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4 - temperature_scaling_factor}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3 - temperature_scaling_factor}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keeping track of step count to use in retry_policy for dynamic temperature adjustment
    state["step_count"] = state.get("step_count", 0) + 1