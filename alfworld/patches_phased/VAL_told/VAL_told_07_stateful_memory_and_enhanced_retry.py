HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = ("Your action wasn't valid. Focus on the admissible actions. "
                         "Consider your recent observations for insight.")
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_locations" not in state:
        state["visited_locations"] = set()
    location_key = observation.split("\n")[0]
    state["visited_locations"].add(location_key)