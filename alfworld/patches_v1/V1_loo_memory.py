HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get('action_guide', '')
    if action_guide:
        prompt += f'\nNote: Consider actions similar to previous successes: {action_guide}.'
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search('<action>(.*?)</action>', response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state['action_guide'] = action
            return action
    return 'examine'

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = 'Recall the guidance on successful actions. Focus on choosing from admissible options.'
        return {'extra_instruction': extra_instruction, 'temperature': 0.5}
    elif attempt == 2:
        extra_instruction = 'Choose an action from admissible options that aligns with previous successes.'
        return {'extra_instruction': extra_instruction, 'temperature': 0.4}
    return None
