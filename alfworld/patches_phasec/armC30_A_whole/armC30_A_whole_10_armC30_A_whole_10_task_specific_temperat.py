HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    task_specific_temperatures = {
        "look_at_obj_in_light": 0.3,
        "pick_and_place_simple": 0.4,
        "pick_clean_then_place_in_recep": 0.35,
        "pick_cool_then_place_in_recep": 0.3,
        "pick_heat_then_place_in_recep": 0.3,
        "pick_two_obj_and_place": 0.4
    }
    task_description = state.get("task_description", "")
    base_temperature = task_specific_temperatures.get(task_description, 0.5)
    
    # Adjust temperature based on attempt number
    if attempt == 1:
        retry_temperature = max(base_temperature - 0.2, 0.2)
    elif attempt == 2:
        retry_temperature = max(base_temperature - 0.3, 0.2)
    else:
        retry_temperature = 0.2

    return {"extra_instruction": extra_instruction, "temperature": retry_temperature}
    
def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "task_description" not in state and "Your task is to:" in observation:
        task_line = next(line for line in observation.split('\n') if "Your task is to:" in line)
        task_description = task_line.split("Your task is to:")[1].strip()
        state["task_description"] = task_description