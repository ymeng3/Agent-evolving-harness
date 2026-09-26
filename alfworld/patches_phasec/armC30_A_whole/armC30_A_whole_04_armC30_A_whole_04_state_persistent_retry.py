HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "extra_retries" not in state:
        state["extra_retries"] = 0
    if attempt == 1:
        state["extra_retries"] += 1
        return {
            "extra_instruction": (
                "Please ensure that the action you choose is one of the admissible ones. "
                "Evaluate the environment and the task requirements carefully."
            ),
            "temperature": 0.3
        }
    elif attempt == 2:
        state["extra_retries"] += 1
        return {
            "extra_instruction": (
                "Your previous attempts were not valid. Focus carefully on selecting a valid action from the list. "
                "Reassess your reasoning about the current situation."
            ),
            "temperature": 0.2
        }
    return None