HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "temperature" not in state:
        state["temperature"] = TEMPERATURE

    def adjust_temperature(current_temp, decrease=True):
        adjustment_factor = 0.1
        new_temp = current_temp - adjustment_factor if decrease else current_temp + adjustment_factor
        return max(0.0, min(new_temp, 1.0))

    extra_instruction = "Your last action wasn't valid. Please carefully select one of the admissible actions."
    
    if attempt == 1:
        state["temperature"] = adjust_temperature(state["temperature"], decrease=True)
        return {"extra_instruction": extra_instruction, "temperature": state["temperature"]}
    elif attempt == 2:
        state["temperature"] = adjust_temperature(state["temperature"], decrease=False)  # Attempt slightly more exploration
        return {"extra_instruction": extra_instruction, "temperature": state["temperature"]}

    return None