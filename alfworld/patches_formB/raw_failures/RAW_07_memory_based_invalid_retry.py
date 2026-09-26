HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # If it's the first invalid attempt, instruct model to focus on admissible actions.
        extra_instruction = "Remember to select only from the admissible actions provided."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # On the second attempt, include recent successful action as a hint to guide the model.
        if "recent_successful_action" in state:
            extra_instruction = (
                f"Recently, you successfully performed the action '{state['recent_successful_action']}'. "
                "Use this as a guideline and remember to choose from the admissible actions."
            )
        else:
            extra_instruction = "Focus on listed admissible actions only."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store the most recent successful action, if it's a valid one.
    if action:
        state["recent_successful_action"] = action