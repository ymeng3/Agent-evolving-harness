HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action was invalid. Carefully review the admissible actions and choose correctly."
    # Attempt to balance exploration vs exploitation by modulating temperature and instruction refinement
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction + " Double-check your choice.", "temperature": 0.25}
    return None