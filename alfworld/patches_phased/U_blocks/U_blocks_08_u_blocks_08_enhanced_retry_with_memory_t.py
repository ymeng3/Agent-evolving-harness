HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Consider what you've seen and done in previous steps."
            " Think about the objects you need and their state."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append((observation, action))
    # Limit memory size to prevent overflow
    if len(state["action_history"]) > 20:
        state["action_history"].pop(0)