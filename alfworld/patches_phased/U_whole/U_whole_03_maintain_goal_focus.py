HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Strip any trailing or leading whitespace and extract the action within <action></action>
    match = re.search(r'<action>(.*?)</action>', response, re.DOTALL)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    # If no valid action is found, return a default action
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None