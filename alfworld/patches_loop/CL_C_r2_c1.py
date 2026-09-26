HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Slightly increase temperature and provide additional instruction
        return {"extra_instruction": " Reassess your previous reasoning and consider the admissible actions again carefully.", "temperature": 0.5}
    return None
