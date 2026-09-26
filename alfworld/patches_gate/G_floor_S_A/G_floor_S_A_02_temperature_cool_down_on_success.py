TEMPERATURE = 0.8

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Cool down the temperature slightly upon successful action to encourage exploration in future steps
    if "successfully" in next_observation:
        state['temperature'] = max(TEMPERATURE - 0.1, 0.3)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Use the updated temperature from memory if set
    retry_temp = state.get('temperature', TEMPERATURE)
    if attempt < 2:
        return {"temperature": retry_temp}
    return None