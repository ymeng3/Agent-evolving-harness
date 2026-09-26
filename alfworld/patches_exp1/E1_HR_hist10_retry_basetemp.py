HISTORY_LENGTH = 10


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Same corrective instruction as A_ops_08, but NO temperature key: the re-query runs at the
    # base temperature (F0 default 0.4), so retry R is separable from the temperature factor T.
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None
