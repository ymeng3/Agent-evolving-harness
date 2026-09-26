def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "The action selected was not admissible. Please ensure to select an action from the admissible list. "
            "Consider the context carefully."
        )
        # Implement varying temperature to explore the impact on generating more diverse choices
        new_temperature = 0.6 if attempt == 1 else 0.8
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None