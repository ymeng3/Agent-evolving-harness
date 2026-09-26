HISTORY_LENGTH = 10
TEMPERATURE = 0.2

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Carefully reconsider the admissible actions and the environment context."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.1}
    return None