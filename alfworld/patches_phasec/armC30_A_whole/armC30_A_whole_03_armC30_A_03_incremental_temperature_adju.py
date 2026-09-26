HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_general = "Your last action wasn't valid. Carefully review the admissible actions and choose one from the list."
    temperatures = {1: 0.45, 2: 0.35}
    if attempt in temperatures:
        return {"extra_instruction": extra_instruction_general, "temperature": temperatures[attempt]}
    return None