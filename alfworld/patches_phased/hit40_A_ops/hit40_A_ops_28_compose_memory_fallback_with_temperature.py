HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Refine retry strategy with memory and temperature adjustments
    if attempt < 2:
        extra_instruction = "Ensure your selected action is one of the admissible actions."
        extra_instruction += " Consider recent unsuccessful actions and attempt different ones."
        if action in state.get('action_history', []) and state['action_history'].count(action) >= 2:
            admissible = [a for a in admissible if a != action]
            extra_instruction += " Avoid repeating excessively used actions."

        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track action history for repeated actions
    if 'action_history' not in state:
        state['action_history'] = []
    state['action_history'].append(action)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Select least repeated admissible action
    action_count = {action: state['action_history'].count(action) for action in admissible}
    return min(action_count, key=action_count.get)