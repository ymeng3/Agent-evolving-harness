HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "last_invalid" not in state:
        state["last_invalid"] = 0
    if attempt == 1:
        state["last_invalid"] += 1
    else:
        state["last_invalid"] = 0

    extra_instruction = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        " You have attempted an invalid action {invalid_attempts} times.".format(invalid_attempts=state["last_invalid"])
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_states" not in state:
        state["visited_states"] = set()
    state["visited_states"].add(observation)