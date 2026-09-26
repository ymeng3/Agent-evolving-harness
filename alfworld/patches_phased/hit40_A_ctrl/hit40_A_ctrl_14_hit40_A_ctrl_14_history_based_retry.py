HISTORY_LENGTH = 7

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    On retry, analyze the last few events to adjust the model's behavior based on history,
    especially on repeated failed actions.
    """
    if attempt == 1:
        hint = "Note recent actions and outcomes to better decide your next step."
        return {"extra_instruction": hint, "temperature": 0.3}
    elif attempt == 2:
        past_actions = [a for _, a in state.get("history", [])[-HISTORY_LENGTH:]]
        repetitive_action = any(past_actions.count(a) > 2 for a in admissible)
        if repetitive_action:
            hint = "Avoid repeating actions which did not succeed in recent steps."
            return {"extra_instruction": hint, "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'history' not in state:
        state['history'] = []
    state['history'].append((observation, action))