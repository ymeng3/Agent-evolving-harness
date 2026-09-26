HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "temperature_trials" not in state:
        state["temperature_trials"] = [0.5, 0.3, 0.2]  # Initial temperature settings for attempts 0, 1, and 2.

    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt < 2:
        if "adaptive_temperatures" not in state:
            state["adaptive_temperatures"] = state["temperature_trials"].copy()

        # Reducing temperature further based on attempt count
        adapted_temperature = max(state["adaptive_temperatures"][attempt] - 0.1, 0.1)
        state["adaptive_temperatures"][attempt] = adapted_temperature
        return {"extra_instruction": extra_instruction, "temperature": adapted_temperature}
    return None