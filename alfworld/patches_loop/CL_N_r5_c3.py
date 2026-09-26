HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Please choose a more contextually appropriate action from the admissible list."
        return {"extra_instruction": extra_instruction}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>(.*?)</action>", response, re.DOTALL)
    if action_match:
        action_text = action_match.group(1).strip().lower()
        if action_text in admissible:
            return action_text
    return ""
