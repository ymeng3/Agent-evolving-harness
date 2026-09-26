HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The chosen action was not valid. Carefully choose from the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    return None


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "known_actions" not in state:
        state["known_actions"] = set()
    
    # Keep track of unique actions taken
    state["known_actions"].add(action)
    
    # Remove actions if memory becomes too large, preserving the last 5
    if len(state["known_actions"]) > 10:
        state["known_actions"] = set(list(state["known_actions"])[-5:])