HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Let's refine your choice. Ensure the action is an exact match from the admissible actions list."
    temperature_values = {1: 0.4, 2: 0.3}
    
    if attempt in temperature_values:
        return {
            "extra_instruction": extra_instruction,
            "temperature": temperature_values[attempt]
        }
    return None