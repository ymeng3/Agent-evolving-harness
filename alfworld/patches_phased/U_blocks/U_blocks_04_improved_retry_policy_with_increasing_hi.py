HISTORY_LENGTH = 15

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Carefully select your next action from the list of admissible actions."
            " Utilize observations and history context for better reasoning."
        )
        return {"extra_instruction": extra_instruction}
    return None