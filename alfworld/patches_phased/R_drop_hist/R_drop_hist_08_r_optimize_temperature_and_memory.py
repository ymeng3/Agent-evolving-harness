TEMPERATURE = 0.45
HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Please carefully examine the admissible actions before selecting."
    new_temperature = {1: 0.25, 2: 0.15}.get(attempt, 0.1)
    return {"extra_instruction": extra_instruction, "temperature": new_temperature} if attempt <= 2 else None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state with newly observed objects to track progression and visited areas.
    if "visited" not in state:
        state["visited"] = set()
    detected_items = [item.lower() for item in next_observation.split() if item.isalpha()]
    state["visited"].update(detected_items)