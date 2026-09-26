def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action was not acceptable in the given context. "
    if attempt == 1:
        # Introduce a balanced approach between flexibility and caution
        extra_instruction += " Carefully consider the list of admissible actions and choose wisely."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}      
    elif attempt == 2:
        # Increase emphasis on the importance of selecting an admissible action
        extra_instruction += " It is crucial to select a valid action. Re-evaluate the current scenario."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None