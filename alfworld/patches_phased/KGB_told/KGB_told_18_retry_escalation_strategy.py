HISTORY_LENGTH = 10


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Introduce escalating guidance for invalid actions
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        hint = "Remember to consider the current observation to make an effective choice."
        return {"extra_instruction": f"{extra_instruction} {hint}"}
    return None