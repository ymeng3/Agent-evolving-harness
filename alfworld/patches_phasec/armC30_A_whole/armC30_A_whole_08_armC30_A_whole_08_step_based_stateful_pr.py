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
    state.setdefault("step_based_guidance", {
        "look_at_obj_in_light": "Ensure to pay attention to the lighting before interacting.",
        "pick_and_place_simple": "Remember the sequence of picking and placing objects carefully.",
        "pick_clean_then_place_in_recep": "Prioritize cleaning the object before placing it.",
        "pick_cool_then_place_in_recep": "Cooling should always precede any action of placing.",
        "pick_heat_then_place_in_recep": "Heat objects correctly before attempting placements.",
        "pick_two_obj_and_place": "Handle two objects simultaneously with precision."
    })
    task_type = state.setdefault("task_type", None)
    if not task_type:
        # Extract task type from the initial task description
        if "Your task is to: " in prompt:
            task_description = prompt.split("Your task is to: ")[1].split("\n")[0]
            for key in state["step_based_guidance"].keys():
                if key in task_description:
                    task_type = key
                    state["task_type"] = key
                    break

    guidance = state["step_based_guidance"].get(task_type, "")
    # Modify the prompt to include task-specific guidance at each step
    return prompt.replace("Now it's your turn to take an action.",
                          f"Now it's your turn to take an action. {guidance}")