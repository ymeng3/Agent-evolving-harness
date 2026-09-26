HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # A combined retry strategy that adjusts temperature and adds extra instructions
    extra_instruction = (
        "The selected action was not admissible. Ensure your selected action is one of the admissible actions. "
        "Reason carefully and ensure you're considering the environment context."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Implement action counting to avoid repeating actions excessively
    if 'action_count' not in state:
        state['action_count'] = {}
    state['action_count'].setdefault(action, 0)
    state['action_count'][action] += 1