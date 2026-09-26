def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "The last action you chose was not valid."
            " Make sure to select one from the list of admissible actions: {}."
            " Consider the environment context and any recent changes.".format(", ".join(admissible))
        )
        return {"extra_instruction": extra_instruction}
    return None