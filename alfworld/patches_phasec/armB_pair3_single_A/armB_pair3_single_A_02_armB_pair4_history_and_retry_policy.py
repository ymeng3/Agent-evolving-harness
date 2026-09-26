HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Enhance the retry policy by adjusting the instruction and temperature for each attempt
    to improve the selection of admissible actions.
    """
    retries = {
        1: {
            "extra_instruction": " The previous action was not valid. Please review the context carefully and select an action from the admissible list that is practical.",
            "temperature": 0.35
        },
        2: {
            "extra_instruction": " This is your last chance. Think carefully and choose one action from the admissible list that fits the situation.",
            "temperature": 0.25
        }
    }
    return retries.get(attempt, None)