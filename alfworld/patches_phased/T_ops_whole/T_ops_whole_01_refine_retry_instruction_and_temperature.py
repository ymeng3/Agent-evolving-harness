HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    refined_instruction = (
        "The previous action choice was invalid. Carefully review the list of admissible actions and "
        "select the most appropriate one that fits the current situation. Pay close attention to the context "
        + "provided in the latest observations."
    )
    if attempt == 1:
        return {"extra_instruction": refined_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": refined_instruction, "temperature": 0.25}
    return None