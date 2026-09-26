def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        clarification_instruction = (
            "Your previously suggested action was invalid. "
            "Please carefully review the admissible actions and the current context of the environment. "
            "Ensure to select an action that aligns with the current goal and is part of the admissible actions list."
        )
        return {
            "extra_instruction": clarification_instruction,
            "temperature": 0.5
        }
    elif attempt == 2:
        clearer_guidance = (
            "It is crucial now to choose an action from the admissible list. "
            "Rethink your previous reasoning, focusing on alignment with the environment's current state and goals."
        )
        return {
            "extra_instruction": clearer_guidance,
            "temperature": 0.3
        }
    
    return None