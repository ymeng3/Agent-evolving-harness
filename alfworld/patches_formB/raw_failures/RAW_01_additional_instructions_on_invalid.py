HISTORY_LENGTH = 8
TEMPERATURE = 0.35

def format_prompt(prompt: str, state: dict) -> str:
    if 'extra_instruction' in state:
        # Append additional instructions to the prompt if any exist in the state.
        prompt += f"\n{state['extra_instruction']}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Extract action within <action> tags if possible
    match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    action = match.group(1).strip().lower() if match else ''
    return action if action in admissible else ''

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt not in state:
        state[attempt] = []
        
    if attempt == 1:
        # If the response has no valid action, add a guiding instruction.
        state[attempt].append(action)
        return {"extra_instruction": "\nRemember to pick an action from the provided admissible actions list.", "temperature": 0.3}
    
    if attempt == 2:
        # If the first retry fails, prompt a more explicit instruction.
        state[attempt].append(action)
        return {"extra_instruction": "\nEnsure you select an action that is explicitly listed as admissible.", "temperature": 0.25}
    
    # Log the invalid actions attempted
    state[attempt].append(action)
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    pass  # No memory mechanism required for this specific patch.

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Default fallback behavior
    return 'look' if 'look' in admissible else admissible[0]