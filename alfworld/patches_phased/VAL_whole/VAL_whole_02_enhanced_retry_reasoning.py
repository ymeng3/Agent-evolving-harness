HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if action not in admissible:
        if attempt == 1:
            extra_instruction = extra_instruction_base + " Look closely at your current environment and reevaluate."
            return {"extra_instruction": extra_instruction, "temperature": 0.3}
        elif attempt == 2:
            extra_instruction = extra_instruction_base + " Consider if there's any pattern mismatch in the chosen action."
            return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None