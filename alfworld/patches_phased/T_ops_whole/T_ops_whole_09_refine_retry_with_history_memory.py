HISTORY_LENGTH = 8
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The chosen action was not valid. Reevaluate your reasoning and consistently select one of the admissible actions below."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()
    state["visited"].add(next_observation)