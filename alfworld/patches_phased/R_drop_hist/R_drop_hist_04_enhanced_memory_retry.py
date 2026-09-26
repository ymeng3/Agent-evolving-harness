TEMPERATURE = 0.5
HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The previous action was invalid. Ensure to select an action from the admissible list."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "history" not in state:
        state["history"] = []
    state["history"].append((observation, action, next_observation))
    if len(state["history"]) > 10:
        state["history"].pop(0)