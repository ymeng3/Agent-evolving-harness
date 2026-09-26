HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize the action count dictionary in state if not already present
    if 'action_count' not in state:
        state['action_count'] = {}
    # Increment the count for the taken action
    state['action_count'][action] = state['action_count'].get(action, 0) + 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Create a variable for instructions to possibly append to the prompt on retry
    instruction = " Your previous action was invalid."
    # Check if the action was repeated over a certain limit
    if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
        admissible = [a for a in admissible if a != action]
        instruction += " Avoid excessive repetition of actions. "
    # Append advisable instruction with emphasis on retry and admissible actions
    instruction += " Focus on the admissible actions provided and choose from them."
    # Adjust the temperature for more deterministic responses
    if attempt == 1:
        return {"extra_instruction": instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None