def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # If an invalid action is detected, compose a more detailed retry strategy that takes into account recent action history
    if attempt == 1:
        # Encourage the model to consider recent unsuccessful actions to avoid repetition and also to focus on valid choices 
        recent_actions = state.get("recent_actions", [])
        non_repeating_actions = [a for a in admissible if a not in recent_actions[-3:]]
        extra_instruction = ("Your previous action was not admissible. "
                             "Review recent actions and ensure you're focusing on the new and admissible ones.")
        return {
            "extra_instruction": extra_instruction, 
            "temperature": 0.35
        }
    elif attempt == 2:
        # Further emphasize using admissible actions while being more deterministic
        extra_instruction = ("It's critical now to select an action from the admissible list. "
                             "Avoid repeating actions from your recent history.")
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.3
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track recent actions to inform retry policy on invalid actions
    if "recent_actions" not in state:
        state["recent_actions"] = []
    # Update recent actions with the latest action, maintaining the length limit
    state["recent_actions"].append(action)
    if len(state["recent_actions"]) > 3:
        state["recent_actions"].pop(0)