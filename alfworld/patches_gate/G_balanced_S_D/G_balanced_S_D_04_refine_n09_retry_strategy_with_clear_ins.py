def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Enhances the retry strategy by adding explicit instructions to clarify the usage of the admissible list.
    """
    new_instruction = (
        "Ensure the action you select is explicitly listed among the admissible actions."
        " Focus on understanding the context and choosing an appropriate action from the list provided."
    )
    
    if attempt == 1:
        # On the first retry, increase detail in the instruction and slightly modify temperature for clarity.
        return {
            "extra_instruction": new_instruction,
            "temperature": 0.35  # Slight adjustment for promoting more deterministic choices.
        }
    elif attempt == 2:
        # Provide emphasized instruction with further temperature adjustment for deterministic behavior.
        return {
            "extra_instruction": new_instruction,
            "temperature": 0.3  # Further reduce temperature for more deterministic output.
        }
    return None