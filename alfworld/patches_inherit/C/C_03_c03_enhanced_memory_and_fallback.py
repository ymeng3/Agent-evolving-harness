HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault("last_observations", []).append(observation)
    if len(state["last_observations"]) > 5:
        state["last_observations"].pop(0)

def choose_fallback(admissible: list[str], state: dict) -> str:
    recent_observations = state.get("last_observations", [])
    check_recent_observation = any("door" in obs for obs in recent_observations)
    return "open door" if check_recent_observation and "open door" in admissible else admissible[0]

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None