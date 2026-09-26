def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "Your previous action was invalid. Please carefully analyze the current situation and ensure your action"
            " is one of the admissible actions. Consider the environment context and your overall goal."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    
    elif attempt == 2:
        extra_instruction = (
            "Once more, the action you chose was not in the list of admissible actions. It is imperative now to"
            " select an action from the given admissible list, while considering the ongoing task context."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    
    return None