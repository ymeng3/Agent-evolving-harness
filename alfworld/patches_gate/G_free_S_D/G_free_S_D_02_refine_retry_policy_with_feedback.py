TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """Refine retry policy by providing targeted feedback after invalid actions."""
    
    if attempt == 1:
        # Provide detailed feedback on what went wrong and guidance for correction
        extra_instruction = (
            "Your previous action was invalid. Ensure your next action is specifically one of the admissible ones."
            " Consider the context and environment when choosing."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    
    elif attempt == 2:
        # Further guidance after a second invalid action, emphasizing caution and context
        extra_instruction = (
            "It's critical to pick an admissible action now. Reflect on the current situation and the provided admissible actions, "
            "and choose carefully."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    
    return None