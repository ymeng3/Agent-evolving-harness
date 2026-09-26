HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "last_invalid_action" in state and state["last_invalid_action"] == action:
        # If the last action was invalid and the same is selected again, try a different strategy.
        extra_instruction = (
            "Your recent attempt to execute a similar action was invalid. Reconsider your reasoning strategy and identify clues from recent observations."
        )
        temperature = 0.6  # Increase temperature to encourage exploration
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    
    if attempt == 1:
        state["last_invalid_action"] = action
        extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction}
    
    if attempt == 2:
        extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction}

    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the state's last invalid action to track loops and avoid repeating the same failed strategy
    if "last_invalid_action" in state and state["last_invalid_action"] == action:
        state["last_invalid_action"] = None  # Reset if action execution moves forward successfully