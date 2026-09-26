HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        state["last_invalid_action"] = action
        feedback = (
            "Your last action '{action}' was invalid. "
            "Carefully consider the admissible actions and make sure to select one."
        ).format(action=action)
        return {"extra_instruction": feedback, "temperature": 0.3}
    elif attempt == 2:
        feedback = (
            "Your action '{action}' was still not valid. Please choose wisely among the admissible actions: {admissible}."
        ).format(action=action, admissible=', '.join(admissible))
        return {"extra_instruction": feedback, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state["last_action"] = action
    state["last_observation"] = observation
    state["next_observation"] = next_observation