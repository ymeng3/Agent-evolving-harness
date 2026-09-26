import random

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {"extra_instruction": "Choose an action from the admissible list and avoid repetitive choices.", "temperature": 0.5}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Track action history to avoid repetition and promote strategic decision-making.
    last_actions = state.get("action_history", [])
    
    # Analyze the recently taken actions to choose a fallback that is less repetitive.
    if last_actions and len(last_actions) >= 2:
        # Check if the last action is repeated and find alternatives.
        if last_actions[-1] in admissible and last_actions[-1] == last_actions[-2]:
            alternate_choices = [action for action in admissible if action != last_actions[-1]]
            if alternate_choices:
                return random.choice(alternate_choices)
    
    move_actions = [action for action in admissible if action.startswith('move')]
    if move_actions:
        return random.choice(move_actions)
    
    # Default to a strategic choice based on admissible actions
    fallback_candidates = ["look", "move", "pick", "open", "close"]
    for action in fallback_candidates:
        for admissible_action in admissible:
            if action in admissible_action:
                return admissible_action

    return random.choice(admissible)