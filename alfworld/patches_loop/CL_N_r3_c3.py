HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "The previous action was not suitable. Please reassess the current "
            "situation and choose another admissible action that better fits "
            "the context you reasoned about."
        )
        return {"extra_instruction": extra_instruction}
    return None
