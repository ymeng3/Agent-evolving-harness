HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        # Adjust the temperature based on the attempt number
        new_temperature = 0.4 - 0.1 * attempt  # Decrease temperature with each retry attempt
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None