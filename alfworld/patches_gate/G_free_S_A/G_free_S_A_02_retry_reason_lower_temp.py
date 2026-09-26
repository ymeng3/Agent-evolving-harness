def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        temperature = 0.3 if attempt == 1 else 0.25
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None