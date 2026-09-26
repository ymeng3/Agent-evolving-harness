HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None