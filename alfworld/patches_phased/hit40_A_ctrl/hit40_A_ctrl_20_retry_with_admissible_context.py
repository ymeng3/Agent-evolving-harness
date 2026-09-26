def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        admissible_text = ", ".join(admissible)
        extra_instruction = (
            "Your previous action was not admissible. "
            "Take another look at the current situation and consider these options carefully: "
            f"{admissible_text}. Make sure to choose an action from the admissible list."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            "This is your final attempt to choose a valid action. "
            "Review the admissible actions thoroughly to make an appropriate choice."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None