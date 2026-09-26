HISTORY_LENGTH = 15
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    additional_instruction = "Carefully reassess your action choices considering the environment observations."
    if attempt == 1:
        return {"extra_instruction": additional_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": additional_instruction, "temperature": 0.4}
    return None