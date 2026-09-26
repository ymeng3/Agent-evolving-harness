HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    task_prompts = {
        "look_at_obj_in_light": "Focus on actions that help examine objects closely.",
        "pick_and_place_simple": "Concentrate on actions to pick and place objects.",
        "pick_clean_then_place_in_recep": "Consider actions to clean and then place objects.",
        "pick_cool_then_place_in_recep": "Choose actions to cool and then place objects.",
        "pick_heat_then_place_in_recep": "Think about actions to heat and then place objects.",
        "pick_two_obj_and_place": "Focus on actions to handle two objects and place them."
    }
    
    def get_task_specific_instruction():
        task_description = state.get("task_description", "")
        for task, prompt in task_prompts.items():
            if task in task_description:
                return prompt
        return ""
    
    extra_instruction = get_task_specific_instruction() + " Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "task_description" not in state:
        task_start_marker = "task is to: "
        start_index = observation.find(task_start_marker)
        if start_index != -1:
            start_index += len(task_start_marker)
            end_index = observation.find("\n", start_index)
            state["task_description"] = observation[start_index:end_index].strip() if end_index != -1 else observation[start_index:].strip()