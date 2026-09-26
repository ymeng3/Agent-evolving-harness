HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Tracking the action history in memory.
    state.setdefault('action_history', []).append(action)

    # Detect repeated action patterns.
    if len(state['action_history']) >= 3:
        last_three_actions = state['action_history'][-3:]
        if last_three_actions[0] == last_three_actions[1] == last_three_actions[2]:
            state['repeat_detected'] = True
        else:
            state['repeat_detected'] = False

    # Clear state if a loop is detected to refresh actions.
    if state.get('repeat_detected', False):
        state['action_history'].clear()
        state['repeat_detected'] = False