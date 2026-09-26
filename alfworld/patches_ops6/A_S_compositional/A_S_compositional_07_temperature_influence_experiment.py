HISTORY_LENGTH = 10
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        # Introducing a slight variation in temperature during retries
        temp_adjustment = 0.8 if attempt == 1 else 0.7
        return {"extra_instruction": extra_instruction, "temperature": temp_adjustment}
    return None