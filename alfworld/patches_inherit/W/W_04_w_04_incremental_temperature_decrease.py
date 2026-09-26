HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action wasn't valid. Concentrate on choosing from the admissible actions provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": state.get("temperature_step", 0.4)}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": state.get("temperature_step", 0.3)}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the temperature_step for incremental decrease in retry_policy on invalid actions
    if "temperature_step" not in state:
        state["temperature_step"] = TEMPERATURE
    else:
        state["temperature_step"] = max(0.1, state["temperature_step"] - 0.1)