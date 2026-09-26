HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "invalid_attempts" not in state:
        state["invalid_attempts"] = 0

    if action not in next_observation:
        state["invalid_attempts"] += 1
    else:
        state["invalid_attempts"] = 0

    if state["invalid_attempts"] >= 2:
        state["dynamic_history"] = max(0, HISTORY_LENGTH - 2)
    else:
        state["dynamic_history"] = HISTORY_LENGTH

def format_prompt(prompt: str, state: dict) -> str:
    history_length = state.get("dynamic_history", HISTORY_LENGTH)
    prompt = prompt.replace(f"{HISTORY_LENGTH}", f"{history_length}")
    return prompt