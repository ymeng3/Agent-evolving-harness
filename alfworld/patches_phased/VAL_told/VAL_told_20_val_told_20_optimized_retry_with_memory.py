HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        state['focus_on_admissible'] = True
        extra_instruction = "Reassess, because your last action wasn't acceptable. Focus on admissible options exclusively." 
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        extra_instruction = "Your action's invalid. Prioritize on choosing from the admissible actions you've seen."
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'focus_on_admissible' in state:
        state.pop('focus_on_admissible')