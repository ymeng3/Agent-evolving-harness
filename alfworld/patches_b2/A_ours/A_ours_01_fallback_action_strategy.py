def choose_fallback(admissible: list[str], state: dict) -> str:
    # Default fallback action is "look", but let's adjust the strategy for selecting a fallback.
    # If among admissible actions, choose an action that is less likely to lead to repetitive behavior
    # and potentially more likely to progress towards objectives like examining objects or locations.
    
    # If "look" is available, favor it as a generally safe exploration option
    if "look" in admissible:
        return "look"
    
    # Otherwise, prioritize less repeated actions in recent memory if that information is available
    if 'action_count' in state:
        # Sort admissible actions by their count (ascending) to favor those used less frequently
        sorted_actions = sorted(admissible, key=lambda action: state['action_count'].get(action, 0))
        return sorted_actions[0]  # Choose the least repeated admissible action
    
    # If no historical data is available, or all admissible actions are fresh, return the first one
    return admissible[0]