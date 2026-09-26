HISTORY_LENGTH = 10
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Please reconsider and choose a different potential action from those available.", "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": "As a final attempt, select an action from the list of admissible actions.", "temperature": 0.4}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    state['retry'] = state.get('retry', 0) + 1
    return random.choice(admissible)