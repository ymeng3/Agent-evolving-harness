HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()
    # Record visited locations and objects to avoid redundant actions
    state["visited"].add(observation)
    state["last_valid_action"] = action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        if "last_valid_action" in state:
            extra_instruction += f" Previously successful action: {state['last_valid_action']}."
        return {"extra_instruction": extra_instruction}
    return None