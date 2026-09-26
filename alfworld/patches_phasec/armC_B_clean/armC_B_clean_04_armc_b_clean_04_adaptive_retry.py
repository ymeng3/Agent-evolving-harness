HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_attempt_1 = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed and evaluate the current situation carefully."
    extra_instruction_attempt_2 = "Your last action wasn't valid again. Reflect more deeply on the task and ensure you understand the context before choosing."
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction_attempt_1, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_attempt_2, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "repeated_actions" not in state:
        state["repeated_actions"] = collections.defaultdict(int)
    state["repeated_actions"][action] += 1