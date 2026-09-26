HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # If the model's action is invalid, retry with a more detailed prompt
    if attempt <= 2 and action not in admissible:
        extra_instruction = "Carefully review the current situation and ensure the action is admissible." if attempt == 1 else "Focus more on the task requirements and ensure your next action is within the allowed options."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state with current step information
    if "steps" not in state:
        state["steps"] = 0
    state["steps"] += 1

    # Track repeated actions to avoid looping
    if "recent_actions" not in state:
        state["recent_actions"] = []
    state["recent_actions"].append(action)
    if len(state["recent_actions"]) > 5:
        state["recent_actions"].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Avoid repeating the last actions, if possible
    for action in admissible:
        if action not in state.get("recent_actions", []):
            return action
    return "look"