HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "Focus on tasks that are directly relevant to immediate goals within the current location. "
            "Re-evaluate any previous assumptions if necessary. "
            "Recall the specific task objectives explicitly to guide action selection."
        )
        incremental_focus = {"extra_instruction": extra_instruction, "temperature": 0.3}
        return incremental_focus
    return None