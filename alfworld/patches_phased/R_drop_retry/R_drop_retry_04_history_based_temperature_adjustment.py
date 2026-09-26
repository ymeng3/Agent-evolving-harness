HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Utilize format_prompt to monitor step progress
    state['current_step'] = state.get('current_step', 0) + 1
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust temperature based on the number of past actions taken
    current_step = state.get('current_step', 1)
    max_steps = 50  # Known maximum steps in typical ALFWorld tasks

    # As the agent progresses through the steps, it uses a lower temperature
    if current_step < max_steps // 3:
        temperature = 0.6
    elif current_step < 2 * max_steps // 3:
        temperature = 0.4
    else:
        temperature = 0.3

    # Retry only if the chosen action is invalid
    return {"extra_instruction": "Please re-assess your choice and select an admissible action.", "temperature": temperature} if attempt < 2 else None