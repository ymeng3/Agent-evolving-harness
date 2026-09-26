HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Carefully select one of the admissible actions."
    state.setdefault("errors", 0)

    if not action in admissible:
        state["errors"] += 1

    if attempt == 1:
        temperature_adjustment = max(0.1, 0.3 - 0.1 * state["errors"])
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustment}
    elif attempt == 2:
        temperature_adjustment = max(0.1, 0.2 - 0.1 * state["errors"])
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustment}
    
    return None