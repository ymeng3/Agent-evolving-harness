HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    action_history = state.setdefault('action_history', [])
    action_history.append(action)
    if len(action_history) > 5:
        action_history.pop(0)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = f"The previous attempt was invalid. The action '{action}' was suggested earlier in similar contexts. Consider alternative actions for your next choice."
        if action in state['action_history'][:-1]:
            admissible = [a for a in admissible if a != action]
            extra_instruction += " Avoid repeating the same action."
        temperature_adjustment = 0.2 if attempt == 1 else 0.3
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustment}
    return None