def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Implements a retry policy with a more effective instruction to re-prompt
    the model when an invalid action is suggested. The instruction will include
    a reminder to select from the admissible actions and to ensure the action
    is practical in the current context.
    """
    retries = {
        1: {
            "extra_instruction": " The previous action was not valid, please ensure you select an action from the admissible list and consider if it is practical in the current context.",
            "temperature": 0.3
        },
        2: {
            "extra_instruction": " This is the final attempt. Carefully select one action from the admissible list and verify its practicality.",
            "temperature": 0.2
        }
    }
    return retries.get(attempt, None)