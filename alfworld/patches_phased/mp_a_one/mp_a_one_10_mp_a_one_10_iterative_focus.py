HISTORY_LENGTH = 12
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = ""
    if attempt == 1:
        extra_instruction = "Reconsider your reasoning. Ensure the selected action is among the admissible ones."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        extra_instruction = "The previous action was still invalid. Please focus on the admissible actions provided, adjust your reasoning accordingly."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()
    state["visited"].add(observation)

def choose_fallback(admissible: list[str], state: dict) -> str:
    preferred_actions = ["look", "examine", "check"]
    for action in preferred_actions:
        if action in admissible:
            return action
    return admissible[0]