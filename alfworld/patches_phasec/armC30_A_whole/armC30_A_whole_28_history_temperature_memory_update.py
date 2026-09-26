HISTORY_LENGTH = 8  # Reduced history length to minimize cognitive load.
TEMPERATURE = 0.3  # Lower temperature to favor more deterministic behavior.

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on the admissible actions and choose wisely. Re-evaluate your reasoning to ensure validity."
    # Add a slight temperature alteration based on attempt to try new avenues gently.
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Maintain a log of visited observations and actions to aid in decision-making.
    state_history = state.setdefault('history', [])
    state_history.append((observation, action))
    state['recent_action'] = action

    # Limit memory size to keep it manageable (affects more complex tasks positively).
    if len(state_history) > 20:
        state_history.pop(0)