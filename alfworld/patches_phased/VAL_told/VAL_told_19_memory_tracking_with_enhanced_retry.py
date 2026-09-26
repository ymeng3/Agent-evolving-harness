HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Enhanced retry logic that adds the last observation to the state for better context management
    if attempt == 1:
        extra_instruction = (
            "Your last action wasn't valid. Re-evaluate the situation and choose "
            "an action from the given list of admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = (
            "Your repeated action wasn't valid. Carefully analyze the context "
            "and ensure the action you choose is within the admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state to track useful observations and actions
    state.setdefault("observations", []).append(observation)
    state.setdefault("actions", []).append(action)
    
    if len(state["observations"]) > HISTORY_LENGTH:
        state["observations"].pop(0)
        state["actions"].pop(0)