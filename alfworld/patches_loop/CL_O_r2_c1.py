HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {"extra_instruction": "Make sure the action chosen matches one of the admissible actions.", "temperature": 0.5}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append((observation, action, next_observation))
