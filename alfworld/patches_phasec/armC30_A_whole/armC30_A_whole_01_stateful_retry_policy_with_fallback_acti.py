HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    fallback_instruction = " If unsure, you might want to choose an exploratory action like 'look around'."
    if attempt == 1:
        state["retry_count"] = state.get("retry_count", 0) + 1
        return {"extra_instruction": extra_instruction_base + fallback_instruction, "temperature": 0.3}
    elif attempt == 2:
        state["retry_count"] = state.get("retry_count", 0) + 1
        return {"extra_instruction": extra_instruction_base, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    if state.get("retry_count", 0) >= 2:
        state["retry_count"] = 0  # Reset retry count after fallback
        exploratory_actions = ["look", "walk forward"]
        valid_exploratory = [action for action in exploratory_actions if action in admissible]
        if valid_exploratory:
            return valid_exploratory[0]
    return admissible[0]