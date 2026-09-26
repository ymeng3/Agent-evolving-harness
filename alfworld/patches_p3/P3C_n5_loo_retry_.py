HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    modified_prompt = 'Remember to stay focused on the task goal at each step. ' + prompt
    return modified_prompt
