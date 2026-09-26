HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. Avoid actions similar to the previous one."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "previous_actions" not in state:
        state["previous_actions"] = []
    state["previous_actions"].append(action)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Default mechanism: extract action from <action> tags
    import re
    match = re.search(r'<action>(.*?)</action>', response, re.I|re.S)
    action = match.group(1).strip().lower() if match else ''
    
    # Check if the action has been recently tried. If it's not found in admissible actions or was performed recently, try another.
    if action in state.get("previous_actions", []):
        for alt_action in admissible:
            if alt_action not in state["previous_actions"]:
                return alt_action.lower()

    return action if action in admissible else ''