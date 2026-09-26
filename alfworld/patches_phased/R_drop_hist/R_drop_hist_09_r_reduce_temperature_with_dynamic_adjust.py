TEMPERATURE = 0.3
HISTORY_LENGTH = 3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action was not valid. Carefully review the admissible actions and prioritize their selection."
    )
    temperature_adjustment = 0.02
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - temperature_adjustment}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - 2 * temperature_adjustment}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'previous_actions' not in state:
        state['previous_actions'] = set()
    state['previous_actions'].add(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Filter the action that hasn't been tried yet, if possible
    unused_actions = [action for action in admissible if action not in state.get('previous_actions', set())]
    if unused_actions:
        return unused_actions[0]
    return admissible[0]