def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Adding more context and guidance for the first retry attempt
        extra_instruction = (
            "Your last action was not in the admissible set."
            " Carefully review the situation and choose an action from the admissible list that reflects the task objectives."
            " Consider if a simple observation action like 'look' could inform a better choice."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        # Further emphasize the importance of selecting from the admissible list with more stern guidance
        extra_instruction = (
            "It's critical to select actions from the admissible list to progress."
            " Reflect on your task and environment context again before deciding your next action."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None