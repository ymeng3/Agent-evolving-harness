HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    """Adjust history length based on task complexity inferred from task description."""
    task_description = prompt.split('task is to: ')[1].split('\n')[0].strip().lower()
    complex_tasks = ['pick_two_obj_and_place', 'pick_clean_then_place_in_recep', 'pick_cool_then_place_in_recep', 'pick_heat_then_place_in_recep']
    state['is_complex'] = any(task in task_description for task in complex_tasks)
    
    if state['is_complex']:
        return prompt.replace(f"most recent {HISTORY_LENGTH} observations", "most recent 10 observations")
    return prompt