HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # Add memory check before issuing a second retry.
        observed_actions = state.get("observed_actions", set())
        if action not in observed_actions:
            observed_actions.add(action)
            state["observed_actions"] = observed_actions
            return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track unique actions taken to enhance memory check in retry
    if "observed_actions" not in state:
        state["observed_actions"] = set()
    state["observed_actions"].add(action)