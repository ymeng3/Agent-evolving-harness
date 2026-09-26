HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    return prompt  # Using default prompt for simplicity

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Record last successful action for strategic fallback
            state['last_successful_action'] = action
            return action
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation and action not in state['action_success']:
        state['action_success'].append(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Pay close attention to the admissible actions and align with past successes."
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = "Consider using an action that has worked well previously."
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Use last successful action as fallback, if it's admissible
    last_successful_action = state.get('last_successful_action')
    if last_successful_action and last_successful_action in admissible:
        return last_successful_action
    return "look"