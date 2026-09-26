HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your previous action was invalid. It seems not suitable based on the admissible action list. "
    if 'loop_detector' not in state:
        state['loop_detector'] = {'latest_invalid_actions': [], 'retry_attempts': 0}

    state['loop_detector']['latest_invalid_actions'].append(action)
    state['loop_detector']['retry_attempts'] += 1

    # Check if last three invalid actions are the same
    if len(state['loop_detector']['latest_invalid_actions']) >= 3:
        last_three_actions = state['loop_detector']['latest_invalid_actions'][-3:]
        if len(set(last_three_actions)) == 1:
            # Prevent repetitive actions when loop detected
            state['loop_detector']['latest_invalid_actions'] = []
            state['loop_detector']['retry_attempts'] = 0
            return {"extra_instruction": extra_instruction_base + "Avoid repeating the same invalid action. Please reason again and choose a different action.", "temperature": 0.3}

    # Decision based on retry attempts
    if state['loop_detector']['retry_attempts'] == attempt:
        # Reset loop detector state when the retry count aligns with the attempt count
        state['loop_detector']['latest_invalid_actions'] = []
        state['loop_detector']['retry_attempts'] = 0
        return {"extra_instruction": extra_instruction_base + "Try to choose an action distinct from recent invalid attempts.", "temperature": 0.35}

    return None