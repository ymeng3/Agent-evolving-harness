HISTORY_LENGTH = 6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if action not in admissible:
        extra_instr = (
            "Re-evaluate your previous choice; the action must be part of the given admissible actions."
            " Ensure alignment with task goals and context."
        )
        return {"extra_instruction": extra_instr, "temperature": 0.3}
    return None
