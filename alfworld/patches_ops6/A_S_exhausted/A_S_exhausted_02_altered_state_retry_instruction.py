HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Refine the retry mechanism by integrating state information into the instruction.
    # This personalized feedback attempts to increase understanding of the current progress.
    if attempt == 1:
        state_info = f"So far, your actions have led to step {state.get('step_count', 0)}. "
        extra_instruction = state_info + "Your last action wasn't valid. Focus more on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        state_info = f"You have attempted {attempt} corrections. Current step is {state.get('step_count', 0)}. "
        extra_instruction = state_info + "Carefully choose your next action from the admissible actions."
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update the state with the current step count to provide more context during retries.
    state['step_count'] = state.get('step_count', 0) + 1