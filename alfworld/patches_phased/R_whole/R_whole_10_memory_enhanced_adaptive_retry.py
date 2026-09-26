HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # Incorporate memory to emphasize state-specific instructions
        state_specific_instruction = "Consider the progress made in prior steps."
        return {"extra_instruction": f"{extra_instruction} {state_specific_instruction}", "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'actions' not in state:
        state['actions'] = []
    state['actions'].append(action)