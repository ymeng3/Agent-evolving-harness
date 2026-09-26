def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        # Refine the additional instruction to be clearer and more concise,
        # focusing specifically on selecting an admissible action.
        extra_instruction = (
            "Your last action was not valid. Select your next action from these admissible options."
        )
        return {"extra_instruction": extra_instruction}
    return None