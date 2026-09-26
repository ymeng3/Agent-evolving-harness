def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible: " + action + 
            ". Please carefully review the current situation and ensure your action is one of the admissible actions: " + 
            ", ".join(admissible) + ". Consider how your action aligns with the task goal."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None