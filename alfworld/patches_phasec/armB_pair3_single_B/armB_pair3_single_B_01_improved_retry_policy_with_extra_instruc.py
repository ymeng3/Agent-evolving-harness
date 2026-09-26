HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 3:
        extra_instruction = (
            "Please ensure your action is valid and matches one of the admissible actions listed. "
            "Double-check your reasoning within <think> tags before presenting your final action."
        )
        return {
            "extra_instruction": extra_instruction,
            "temperature": max(0.2, TEMPERATURE - 0.1 * attempt)
        }
    return None