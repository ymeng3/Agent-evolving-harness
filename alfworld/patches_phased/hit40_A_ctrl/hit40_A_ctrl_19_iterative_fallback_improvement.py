def choose_fallback(admissible: list[str], state: dict) -> str:
    # Check if the action was previously attempted and increment its counter
    state.setdefault("action_attempt_count", {})
    
    def score_action(action):
        return state["action_attempt_count"].get(action, 0)

    # Sort admissible actions based on how many times they were attempted before
    sorted_actions = sorted(admissible, key=score_action)
    
    # Choose the action with the least attempts as the fallback
    if sorted_actions:
        chosen_action = sorted_actions[0]
        state["action_attempt_count"][chosen_action] = state["action_attempt_count"].get(chosen_action, 0) + 1
        return chosen_action
    
    # Default to 'look' if no admissible action is available
    return "look"