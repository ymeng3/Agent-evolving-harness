HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Adding a strategy note to the prompt to encourage more thoughtful action selection
    strategy_note = "Analyze your position critically and ensure that the selected action directly correlates with admissible actions for effectiveness."
    return f"{prompt}\n{strategy_note}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Prompt the model to reconsider its approach with a lower temperature on the first failure
        extra_instruction = "Your previous action was invalid. Carefully reevaluate the current observation and admissible actions to improve accuracy."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # On the second failure, further lower the temperature to encourage more deterministic choices
        extra_instruction = "Focus on selecting one of the admissible actions explicitly listed to ensure a valid choice."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Record the last action and observation for potential future use
    state['last_action'] = action
    state['last_observation'] = observation

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize a new action based on previous unsuccessful attempts
    last_action = state.get('last_action', None)
    if last_action and last_action in admissible:
        # If the last action is still admissible, try something different if we got here by retry_policy
        return next((a for a in admissible if a != last_action), admissible[0])
    return admissible[0]