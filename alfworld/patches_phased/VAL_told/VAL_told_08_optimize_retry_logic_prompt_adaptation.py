HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 3:
        instructions = [
            "Note: Your previous choice was invalid. Concentrate on selecting a valid option from the list.",
            "Reminder: Please ensure your action is from the admissible actions provided.",
            "Caution: The action must match one of the admissible actions exactly. Double-check before proceeding."
        ]
        return {"extra_instruction": instructions[attempt - 1]}
    return None