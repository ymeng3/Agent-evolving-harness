HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {'extra_instruction': 'Ensure your action is valid and based on the current context.', 'temperature': 0.5}
    elif attempt == 2:
        return {'extra_instruction': 'Reflect on previous steps to make an admissible choice.', 'temperature': 0.6}
    return None
