HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    temperatures = [0.5, 0.7]
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": temperatures[0]}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": temperatures[1]}
    return None