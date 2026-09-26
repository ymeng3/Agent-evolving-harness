HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            f"Based on your observation: '{state.get('last_observation', 'unknown')}', "
            f"please choose a more contextually appropriate action from the admissible list."
        )
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['last_observation'] = observation
