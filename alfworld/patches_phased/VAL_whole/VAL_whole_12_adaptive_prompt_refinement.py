HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = ("Your last action wasn't valid. Carefully review the current observation and consider "
                             "the logical consequences of each admissible action. Pick the action that best aligns "
                             "with achieving the goal.")
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = ("Once again, your previous action was invalid. Concentrate on the immediate needs in "
                             "the environment and ensure your choice of action is among the admissible ones. "
                             "Think about the likely outcomes.")
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None