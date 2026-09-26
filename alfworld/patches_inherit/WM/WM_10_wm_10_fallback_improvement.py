HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Use a vote-based approach to choose the fallback
    # Count frequency of each action based on history and choose the less frequent admissible one
    action_frequency = {action: 0 for action in admissible}
    for obs_action in state.get("action_history", []):
        past_action = obs_action[1]
        if past_action in action_frequency:
            action_frequency[past_action] += 1
    
    # Select the action with the minimum frequency
    fallback_action = min(admissible, key=lambda a: action_frequency.get(a, 0))
    return fallback_action

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the state with a history of actions
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append((observation, action))