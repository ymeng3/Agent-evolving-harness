TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        instruction = "Your previously selected action was invalid. Please reevaluate the situation carefully, considering all observations and the task goal, before choosing a new admissible action."
        return {"extra_instruction": instruction}
    elif attempt == 2:
        instruction = "The chosen action was still not admissible. Think deeply about the environment context and how each action aligns with the task objective."
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None