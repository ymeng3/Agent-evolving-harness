HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {"extra_instruction": "Re-evaluate the current state and ensure the action is valid.", "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    visited = state.setdefault("visited", set())
    visited.add(observation)
