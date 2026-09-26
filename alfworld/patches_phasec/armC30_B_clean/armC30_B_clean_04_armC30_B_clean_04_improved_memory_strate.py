HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    
    # Determine if the action involves a receptacle
    if "place" in action or "put" in action:
        receptacle_match = re.search(r'\b(?:in|on|into)\s+(\w+)', action)
        if receptacle_match:
            receptacle_name = receptacle_match.group(1)
            state["visited_receptacles"].add(receptacle_name)
    
    # Update observation notes
    if "observation_notes" not in state:
        state["observation_notes"] = []
    state["observation_notes"].append((observation, action, next_observation))