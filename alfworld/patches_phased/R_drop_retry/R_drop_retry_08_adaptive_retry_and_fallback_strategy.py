HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Retry with more constrained prompts and adjusted temperature on consecutive failures
    if attempt == 1:
        # First retry, tighten the temperature slightly and add extra clarification in the prompt
        return {"extra_instruction": "Ensure the action is one of the options and relates to the current goal.", "temperature": 0.4}
    elif attempt == 2:
        # Second retry, further lower the temperature to increase focus
        return {"extra_instruction": "Select the most appropriate action from the list of admissibles.", "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the fallback action based on a heuristic for likely options when the correct action fails
    # Prioritize 'look' if available, otherwise default to the first option
    fallback_priorities = ["look", "explore", "examine"]
    
    for priority_action in fallback_priorities:
        for action in admissible:
            if priority_action in action:
                return action
    
    # If none of the priority actions are admissible, choose the first option
    return admissible[0]