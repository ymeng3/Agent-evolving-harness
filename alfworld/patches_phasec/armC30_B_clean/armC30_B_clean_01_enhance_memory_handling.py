HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": "Re-evaluate your decision carefully and choose from the admissible actions."}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault('visited_states', set()).add(observation)
    if len(state['visited_states']) > 50:  # Arbitrary large number to keep memory scalable
        state['visited_states'].pop()