TEMPERATURE = 0.3
HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Exactly the corrective-instruction retry that frozen MECH03 realized (its memory/prompt hooks were inert at runtime):
    # re-query on an inadmissible action with a corrective instruction and temperature 0.3 - 0.05 * attempt.
    if action in admissible:
        return None
    extra_instruction = (
        f"Observed action: '{action}' is not in the admissible actions list. "
        "Remember to use only the actions provided. Consider revisiting your reasoning."
    )
    return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - 0.05 * attempt}
