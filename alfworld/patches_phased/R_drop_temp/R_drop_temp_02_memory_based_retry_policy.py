HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        state['last_attempt_invalid'] = True
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if state.get('last_attempt_invalid'):
        state['last_attempt_invalid'] = False
        admissibles_with_priority = sorted(admissible, key=lambda x: ('examine' in x, 'pick' in x), reverse=True)
        state['priority_admissibles'] = admissibles_with_priority