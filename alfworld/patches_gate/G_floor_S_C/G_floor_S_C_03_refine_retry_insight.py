def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        # Provide a more tailored instruction focusing on insights from the response.
        extra_instruction = (
            f"Your previous action '{action}' was not admissible. "
            "Consider your reasoning: "
            f"{response}. "
            "Focus carefully on relevant observations, ensure the chosen action is one of the admissible actions, and double-check the current context."
        )
        return {"extra_instruction": extra_instruction}
    return None