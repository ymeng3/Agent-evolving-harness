HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    prioritized_tasks = ['pick_and_place_simple', 'pick_clean_then_place_in_recep', 'pick_cool_then_place_in_recep',
                         'pick_heat_then_place_in_recep', 'pick_two_obj_and_place']
    for task in prioritized_tasks:
        if task in prompt and 'task_priority' not in state:
            state['task_priority'] = task
            break

    if 'task_priority' in state:
        additional_context = f" You are working on a prioritized task: {state['task_priority']}. Ensure consistent actions relevant to this task."
        return prompt + additional_context
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update task priorities based on observations and actions for potential new strategies in future steps
    if 'visited_locations' not in state:
        state['visited_locations'] = set()
    state['visited_locations'].add(observation)

    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)

    if len(state['action_history']) > 20:
        state['action_history'].pop(0)