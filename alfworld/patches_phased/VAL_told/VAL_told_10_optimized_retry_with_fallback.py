HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on selecting one of the admissible actions. Think through your reasoning carefully."
    if attempt == 1:
        new_temperature = 0.4  # Make the temperature adjustment less drastic to retain more variability.
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer the first admissible action as the fallback to ensure a consistent and less random choice.
    return admissible[0] if admissible else 'look'