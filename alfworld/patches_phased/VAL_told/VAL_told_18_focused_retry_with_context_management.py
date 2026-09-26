HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Truncate or limit details that may distract the model.
    # Keep the focus on current observation and admissible actions.
    start_idx = prompt.find("Your admissible actions")
    return prompt[start_idx:] if start_idx != -1 else prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    if match:
        proposed_action = match.group(1).strip().lower()
        if proposed_action in admissible:
            return proposed_action
    # Default fallback if no valid action is found
    state['last_invalid_response'] = response  # Store last invalid response for insight
    return 'look'

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = ("Your recent action was invalid. Reflect on the scenario again, concentrating "
                             "on the current observation and admissible actions.")
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        extra_instruction = ("Once more, reassess your action choice. It's crucial to choose from "
                             "the provided valid options.")
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Log pertinent observations, actions, and invalid responses
    if 'history' not in state:
        state['history'] = []
    state['history'].append((observation, action, next_observation))
    if len(state['history']) > 20:  # Maintain a reasonable memory size
        state['history'].pop(0)
    
def choose_fallback(admissible: list[str], state: dict) -> str:
    # If there are previous invalid actions, exclude their next potential outcomes
    last_invalid = state.get('last_invalid_response', None)
    if last_invalid:
        for action in admissible:
            if action not in last_invalid:
                return action
    return 'look'