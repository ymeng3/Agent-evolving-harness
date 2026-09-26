HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        new_temperature = max(0.3, TEMPERATURE - attempt * 0.1)
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None