def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Modifies the retry strategy by adjusting the temperature and providing detailed
    reinforcement instructions on each invalid attempt to guide the agent.
    """
    if attempt == 1:
        extra_instruction = (
            "Your last action was invalid. Carefully analyze the admissible actions, "
            "consider the task requirements, and choose an action wisely."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            "This is your final chance to select a valid action. Reinforce your understanding "
            "of the admissible actions, cross-check with the task context, and make an accurate selection."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None