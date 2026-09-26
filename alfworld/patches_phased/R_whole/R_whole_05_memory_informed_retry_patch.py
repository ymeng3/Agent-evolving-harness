HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize memory for visited observations and repeated actions
    if "visited_observations" not in state:
        state["visited_observations"] = set()
    if "repeated_actions" not in state:
        state["repeated_actions"] = {}

    # Add the current observation to visited observations
    state["visited_observations"].add(observation)

    # Track repeated actions
    if action not in state["repeated_actions"]:
        state["repeated_actions"][action] = 0
    state["repeated_actions"][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if action in state.get("repeated_actions", {}) and state["repeated_actions"][action] > 2:
        extra_instruction += " Avoid repeating the same invalid action."
        
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None