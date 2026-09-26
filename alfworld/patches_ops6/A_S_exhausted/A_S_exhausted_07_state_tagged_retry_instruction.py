HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # New mechanism: Embedding state information within retry instructions
    # to guide decision-making more contextually based on episode state.
    state_info = f" Prior state notes: {state.get('notes', 'None')}"
    extra_instruction = f"Your last action wasn't valid.{state_info} Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track notes about the environment to inform retry instructions later.
    if 'notes' not in state:
        state['notes'] = "Initial notes."
    state['notes'] = f"Action taken: {action}. Last observation: {observation}"