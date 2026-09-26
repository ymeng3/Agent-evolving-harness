HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        if 'look' in action:
            extra_instruction = "Actions involving 'look' are often less effective here. Focus on goal-oriented actions."
        else:
            extra_instruction = 'Try to select the most relevant action that aligns with your reasoning.'
        return {'extra_instruction': extra_instruction}
    elif attempt == 2:
        extra_instruction = 'Carefully reevaluate the context and choose an action closely matching the required goal.'
        return {'extra_instruction': extra_instruction, 'temperature': 0.3}
    return None
