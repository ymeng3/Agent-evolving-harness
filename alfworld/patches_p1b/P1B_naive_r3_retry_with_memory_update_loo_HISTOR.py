def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = 'Please choose a more contextually appropriate action from the admissible list.'
        return {'extra_instruction': extra_instruction}
    return None
