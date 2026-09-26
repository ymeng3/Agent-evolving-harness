HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if 'invalid_attempts' not in state:
        state['invalid_attempts'] = 0

    if action not in admissible:
        state['invalid_attempts'] += 1

    extra_instruction = "Your last action wasn't valid. Focus on choosing an admissible action from the list provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'invalid_attempts' in state and state['invalid_attempts'] > 0:
        state['invalid_attempts'] = 0

def choose_fallback(admissible: list[str], state: dict) -> str:
    return admissible[0]