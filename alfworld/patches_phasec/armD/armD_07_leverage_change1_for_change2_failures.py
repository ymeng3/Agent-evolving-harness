HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # On the first attempt, encourage better reasoning by re-prompting with clarification
        extra_instruction = (
            "The action you suggested is not admissible. Focus on the current admissible actions "
            "and ensure your response includes correct format by thoroughly verifying the "
            "available options rather than re-evaluating unseen contexts."
        )
        return {
            "extra_instruction": extra_instruction,
            "temperature": min(TEMPERATURE + 0.1, 1.0)
        }
    return None