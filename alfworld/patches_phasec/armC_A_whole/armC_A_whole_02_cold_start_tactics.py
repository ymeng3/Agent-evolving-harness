HISTORY_LENGTH = 8
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    attempt_temperature = {1: 0.2, 2: 0.1}
    extra_instruction = (
        "Your last action wasn't valid. Concentrate on picking exactly one of the "
        "admissible actions mentioned. Take into account the current context and "
        "prior knowledge from observations."
    )
    if attempt in attempt_temperature:
        return {"extra_instruction": extra_instruction, "temperature": attempt_temperature[attempt]}
    return None