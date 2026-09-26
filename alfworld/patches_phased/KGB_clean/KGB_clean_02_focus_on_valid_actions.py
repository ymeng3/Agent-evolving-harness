HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Your previous action was invalid. Carefully choose from the admissible actions."}
    elif attempt == 2:
        return {"extra_instruction": "Attempt again, ensuring the action is one of the admissible ones."}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    action_match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    action = action_match.group(1).strip().lower() if action_match else ''

    return action if action in admissible else 'look'