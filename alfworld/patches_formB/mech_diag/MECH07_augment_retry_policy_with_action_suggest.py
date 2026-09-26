HISTORY_LENGTH = 4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        suggested_actions = ', '.join(admissible[:3])  # Suggest the first three admissible actions
        extra_instruction = (
            f"The action you chose was not among the admissible actions. "
            f"Here are a few suggested actions: {suggested_actions}. "
            "Please select an action from the admissible list."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None