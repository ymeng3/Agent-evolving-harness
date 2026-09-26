HISTORY_LENGTH = 15
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous attempt was not valid. Please focus on choosing one of the listed admissible actions."
    if "retry_count" not in state:
        state["retry_count"] = 0
        
    state["retry_count"] += 1

    state_instruction = f" You have retried {state['retry_count']} times."
    if attempt == 1:
        return {"extra_instruction": extra_instruction + state_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction + state_instruction, "temperature": 0.2}
    return None