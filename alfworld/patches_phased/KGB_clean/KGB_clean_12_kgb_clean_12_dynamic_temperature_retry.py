HISTORY_LENGTH = 10

TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action was invalid. Please choose wisely from the listed admissible actions."
    if attempt == 1:
        state.setdefault("retry_attempts", 0)
        state["retry_attempts"] += 1
        return {"extra_instruction": extra_instruction, "temperature": max(0.3, TEMPERATURE - state["retry_attempts"] * 0.1)}
    elif attempt == 2:
        state["retry_attempts"] += 1
        return {"extra_instruction": extra_instruction, "temperature": max(0.3, TEMPERATURE - state["retry_attempts"] * 0.1)}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "retry_attempts" in state:
        state["retry_attempts"] = 0