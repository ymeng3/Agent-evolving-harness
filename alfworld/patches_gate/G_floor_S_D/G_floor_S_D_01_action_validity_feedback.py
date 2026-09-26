def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Wrapper function to log why an action was rejected.
    def log_rejection(reason):
        if "rejection_reasons" not in state:
            state["rejection_reasons"] = []
        state["rejection_reasons"].append(reason)

    # Extract the action between the <action> tags.
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["last_valid_action"] = action
            return action
        else:
            log_rejection(f"Action '{action}' not in admissible list.")
    else:
        # If no action is found, log a rejection reason.
        log_rejection("No action tag found in response.")

    # Use the last valid action if present to ensure action continuity.
    if "last_valid_action" in state:
        log_rejection("Using last valid action for continuity.")
        return state["last_valid_action"]
    
    # Default to 'look' if all else fails.
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Clear rejection reasons each step, preparing for the next.
    state["rejection_reasons"] = []