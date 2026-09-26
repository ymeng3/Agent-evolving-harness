HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_memory" not in state:
        state["action_memory"] = []
    state["action_memory"].append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    unique_actions = set(state.get("action_memory", []))
    fallback_options = [action for action in admissible if action not in unique_actions]
    return fallback_options[0] if fallback_options else 'look'