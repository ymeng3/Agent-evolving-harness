mechanism_family_steps = {
    "look_at_obj_in_light": ["find the object", "go to the light source", "pick up the object", "place it under the light source"],
    "pick_and_place_simple": ["find the object", "pick it up", "find the receptacle", "place the object into the receptacle"],
    "pick_clean_then_place_in_recep": ["find the object", "pick it up", "clean the object", "find the receptacle", "place the object into the receptacle"],
    "pick_cool_then_place_in_recep": ["find the object", "pick it up", "cool the object", "find the receptacle", "place the object into the receptacle"],
    "pick_heat_then_place_in_recep": ["find the object", "pick it up", "heat the object", "find the receptacle", "place the object into the receptacle"],
    "pick_two_obj_and_place": ["find the first object", "pick it up", "find the second object", "pick it up", "find the receptacle", "place both objects into the receptacle"]
}

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    task_family = state.get("task_family")
    if not task_family:
        if "light" in observation:
            state["task_family"] = "look_at_obj_in_light"
        elif "simple" in observation:
            state["task_family"] = "pick_and_place_simple"
        elif "clean" in observation:
            state["task_family"] = "pick_clean_then_place_in_recep"
        elif "cool" in observation:
            state["task_family"] = "pick_cool_then_place_in_recep"
        elif "heat" in observation:
            state["task_family"] = "pick_heat_then_place_in_recep"
        elif "two" in observation:
            state["task_family"] = "pick_two_obj_and_place"
            
    task_steps = mechanism_family_steps.get(task_family)
    state["progress"] = (state.get("progress", 0) + 1) % len(task_steps)

def format_prompt(prompt: str, state: dict) -> str:
    task_family = state.get("task_family")
    progress = state.get("progress", 0)
    
    if task_family:
        extra_guidance = f"Following the strategy for {task_family.replace('_', ' ')} tasks, you should now {mechanism_family_steps[task_family][progress]}."
        return prompt + "\n" + extra_guidance
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>(.*?)</action>", response)
    if action_match:
        proposed_action = action_match.group(1).strip().lower()
        if proposed_action in admissible:
            return proposed_action

    if "place" in task_family:
        for action in admissible:
            if "place" in action:
                return action
    return random.choice(admissible)