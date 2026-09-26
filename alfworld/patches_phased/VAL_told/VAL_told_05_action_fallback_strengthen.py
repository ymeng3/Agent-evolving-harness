HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    return prompt  # Using default prompt format for simplicity

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    return None  # Fallback to retry policy

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please try again. The last action was not valid. Choose from the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    import random
    # Randomly choose an admissible action to ensure progress
    return random.choice(admissible)