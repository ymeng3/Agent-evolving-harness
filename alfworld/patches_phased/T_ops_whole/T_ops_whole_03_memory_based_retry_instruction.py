HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    incorrect_actions = state.get("incorrect_actions", set())
    incorrect_actions.add(action)
    state["incorrect_actions"] = incorrect_actions
    extra_instruction = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    )
    if attempt == 1:
        extra_instruction += " Avoid actions you've tried and failed before: " + ", ".join(incorrect_actions) + "."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction += " As a reminder, avoid these actions: " + ", ".join(incorrect_actions) + "."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    incorrect_actions = state.get("incorrect_actions", set())
    if next_observation != "action_completed":  # Or some other condition that signifies failure
        incorrect_actions.add(action)
    state["incorrect_actions"] = incorrect_actions