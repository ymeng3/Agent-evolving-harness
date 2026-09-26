HISTORY_LENGTH = 10
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Carefully analyze the situation and choose an admissible action."
    temperature_adjustment = {1: 0.4, 2: 0.3}
    new_temperature = temperature_adjustment.get(attempt, 0.2)
    return {"extra_instruction": extra_instruction, "temperature": new_temperature}