HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_states" not in state:
        state["visited_states"] = set()
    # Save the current observation
    state["visited_states"].add(next_observation)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r'<action>(.*?)</action>', response)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            return action
        # Check for re-exploring known states and prevent it
        if state.get("visited_states") and len(state["visited_states"]) >= 3:
            for adm_action in admissible:
                if "look" not in adm_action:
                    return adm_action
    # Default fallback to look if something goes wrong or action isn't intended
    return "look"