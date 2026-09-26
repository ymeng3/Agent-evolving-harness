HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Reduce the temperature as retry attempts increase.
    extra_instruction = "Your last action wasn't valid. Please select an admissible action."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.15}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store the last action and observation to avoid repeating them.
    state["last_observation"] = observation
    state["last_action"] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Select a fallback action avoiding repetition of the last unsuccessful action.
    last_action = state.get("last_action", "")
    filtered_admissible = [a for a in admissible if a != last_action]

    # If no admissible action remains, default to the first option.
    return filtered_admissible[0] if filtered_admissible else admissible[0]