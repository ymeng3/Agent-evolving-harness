HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        
        # Check if the last three actions are the same and avoid repeating
        if "last_actions" in state and len(state["last_actions"]) >= 3:
            last_three = state["last_actions"][-3:]
            if all(a == action for a in last_three):
                extra_instruction += " Avoid repeating the same action."
        
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "last_actions" not in state:
        state["last_actions"] = []
    
    # Update the action history
    state["last_actions"].append(action)
    if len(state["last_actions"]) > 5:  # Keep only the last 5 actions to check for repetition
        state["last_actions"].pop(0)
