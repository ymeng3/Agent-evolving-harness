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
    if "observations_actions" not in state:
        state["observations_actions"] = []
    state["observations_actions"].append((observation, action))

def choose_fallback(admissible: list[str], state: dict) -> str:
    last_observation_actions = state.get("observations_actions", [])
    if last_observation_actions:
        last_observation, last_action = last_observation_actions[-1]
        fallback_action = next((action for obs, action in reversed(last_observation_actions) if action in admissible), None)
        if fallback_action:
            return fallback_action
    return admissible[0] if admissible else 'look'