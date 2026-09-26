HISTORY_LENGTH = 12

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Your last action was not valid. Carefully select one from the listed admissible actions."
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        extra_instruction = ("Your previous actions were invalid. Evaluate the current scenario thoroughly and " 
                             "choose the most relevant admissible action.")
        return {"extra_instruction": extra_instruction, "temperature": 0.3} # Lower temperature for more deterministic result.
    return None

TEMPERATURE = 0.35

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # A simple memory strategy to track action frequency to detect loops
    if 'action_count' not in state:
        state['action_count'] = {}
    if action in state['action_count']:
        state['action_count'][action] += 1
    else:
        state['action_count'][action] = 1

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose the least frequent action first if looping is detected
    if state.get('action_count'):
        least_frequent_action = min(admissible, key=lambda x: state['action_count'].get(x, 0))
        return least_frequent_action
    return 'look'