HISTORY_LENGTH = 8
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    state.setdefault("previous_invalid_action", 0)
    
    if state["previous_invalid_action"] > 3:  # If more than 3 invalid actions have been encountered
        return {"extra_instruction": "You seem to be making a lot of invalid actions. Carefully examine the admissible actions and select one.", "temperature": 0.2}
    
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperature_adjustments = {1: 0.4, 2: 0.3, 3: 0.2}
    
    # Adjust temperature based on attempt
    if attempt in temperature_adjustments:
        state["previous_invalid_action"] += 1
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustments[attempt]}
    
    return None