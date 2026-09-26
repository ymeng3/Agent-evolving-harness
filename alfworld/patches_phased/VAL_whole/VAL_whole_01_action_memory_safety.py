HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    action_log = state.setdefault("action_log", set())
    action_log.add(action)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_log = state.get("action_log", set())
    
    # Extract the action within <action>...</action>
    action_match = re.search(r"<action>(.*?)</action>", response.strip(), re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        # Check if the action is admissible and not repeated
        if action in admissible and action not in action_log:
            return action

    # Default to first admissible action not already taken
    for admissible_action in admissible:
        if admissible_action not in action_log:
            return admissible_action
    
    # Fallback to first admissible action if all have been tried
    return admissible[0]