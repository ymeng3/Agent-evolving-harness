HISTORY_LENGTH = 10

TASK_TEMPERATURE_SETTINGS = {
    "look_at_obj_in_light": 0.3,
    "pick_and_place_simple": 0.5,
    "pick_clean_then_place_in_recep": 0.6,
    "pick_cool_then_place_in_recep": 0.7,
    "pick_heat_then_place_in_recep": 0.6,
    "pick_two_obj_and_place": 0.5,
}

def format_prompt(prompt: str, state: dict) -> str:
    task_name_extractor = lambda description: description.split(' ')[0]
    task_name = task_name_extractor(prompt)
    state["temperature"] = TASK_TEMPERATURE_SETTINGS.get(task_name, 0.5)
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "You must choose an action from the list of admissible actions.", "temperature": state["temperature"]}
    elif attempt == 2:
        return {"temperature": state["temperature"]}
    return None